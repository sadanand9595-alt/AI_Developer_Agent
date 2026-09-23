from uuid import uuid4

from fastapi.testclient import TestClient

from api.app import app
from database.repositories.task_repository import TaskRepository
from database.session import session_scope
from services.task_service import TaskService


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4()}@example.com"


def _register_and_login(
    client: TestClient,
    *,
    prefix: str,
    password: str = "correct-horse-battery",
) -> tuple[str, str]:
    """Register and login a fresh user. Returns (token, user_id)."""

    email = _unique_email(prefix)

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "name": f"{prefix} User",
            "password": password,
        },
    )

    assert register_response.status_code == 201, (
        register_response.text
    )

    user_id = register_response.json()["id"]

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200, (
        login_response.text
    )

    return (
        login_response.json()["access_token"],
        user_id,
    )


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def _create_running_task(
    user_id: str,
) -> tuple[str, str]:
    """Create a durable RUNNING task and return (task_id, execution_id)."""

    with session_scope() as session:
        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user_id,
            title="Execution Pause Resume API Test",
            description="Testing manual execution pause and resume.",
        )

        execution_id = f"api-pause-{uuid4()}"

        started = task_service.start_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert started.status == "running"
        assert started.execution_id == execution_id
        assert started.lease_owner_id == execution_id

        return task.id, execution_id


def test_pause_execution_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/executions/unauthenticated-execution/pause",
        )

    assert response.status_code == 401


def test_resume_execution_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/executions/unauthenticated-execution/resume",
        )

    assert response.status_code == 401


def test_pause_execution_unknown_execution_returns_404() -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="execution-pause-unknown",
        )

        response = client.post(
            "/executions/unknown-execution-id/pause",
            headers=_auth_headers(token),
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Execution not found."


def test_pause_execution_foreign_user_returns_404() -> None:
    with TestClient(app) as client:
        owner_token, owner_id = _register_and_login(
            client,
            prefix="execution-pause-owner",
        )

        attacker_token, _ = _register_and_login(
            client,
            prefix="execution-pause-attacker",
        )

        task_id, execution_id = _create_running_task(owner_id)

        response = client.post(
            f"/executions/{execution_id}/pause",
            headers=_auth_headers(attacker_token),
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Execution not found."

        with session_scope() as session:
            task = TaskRepository(session).get_by_id(task_id)

            assert task is not None
            assert task.status == "running"
            assert task.execution_id == execution_id
            assert task.lease_owner_id == execution_id

        assert owner_token


def test_pause_and_resume_execution_success() -> None:
    with TestClient(app) as client:
        token, user_id = _register_and_login(
            client,
            prefix="execution-pause-resume-success",
        )

        task_id, execution_id = _create_running_task(user_id)

        # -------------------------------------------------
        # PAUSE
        # -------------------------------------------------

        response = client.post(
            f"/executions/{execution_id}/pause",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200, response.text

        pause_payload = response.json()

        assert pause_payload["execution_id"] == execution_id
        assert pause_payload["task_id"] == task_id
        assert pause_payload["status"] == "paused"

        with session_scope() as session:
            task = TaskRepository(session).get_by_id(task_id)

            assert task is not None
            assert task.status == "paused"
            assert task.execution_id == execution_id

            # Manual pause releases the active worker lease.
            assert task.lease_owner_id is None
            assert task.lease_expires_at is None
            assert task.last_heartbeat_at is None

            paused_retry_count = task.retry_count

        # -------------------------------------------------
        # RESUME
        # -------------------------------------------------

        response = client.post(
            f"/executions/{execution_id}/resume",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200, response.text

        resume_payload = response.json()

        assert resume_payload["execution_id"] == execution_id
        assert resume_payload["task_id"] == task_id
        assert resume_payload["status"] == "running"

        with session_scope() as session:
            task = TaskRepository(session).get_by_id(task_id)

            assert task is not None
            assert task.status == "running"

            # Execution identity must survive pause/resume.
            assert task.execution_id == execution_id

            # Resume must acquire a fresh execution lease.
            assert task.lease_owner_id == execution_id
            assert task.lease_expires_at is not None
            assert task.last_heartbeat_at is not None

            # Pause/resume is not a retry.
            assert task.retry_count == paused_retry_count


def test_resume_execution_from_non_paused_task_returns_conflict() -> None:
    with TestClient(app) as client:
        token, user_id = _register_and_login(
            client,
            prefix="execution-resume-invalid-state",
        )

        task_id, execution_id = _create_running_task(user_id)

        response = client.post(
            f"/executions/{execution_id}/resume",
            headers=_auth_headers(token),
        )

        assert response.status_code == 409, response.text

        with session_scope() as session:
            task = TaskRepository(session).get_by_id(task_id)

            assert task is not None
            assert task.status == "running"
            assert task.execution_id == execution_id
            assert task.lease_owner_id == execution_id
