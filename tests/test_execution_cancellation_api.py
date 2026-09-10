from uuid import uuid4

from fastapi.testclient import TestClient

from api.app import app
from database.session import session_scope
from database.repositories.task_repository import TaskRepository
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
    """
    Create a durable running Task and return
    (task_id, execution_id).
    """

    with session_scope() as session:
        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user_id,
            title="Execution Cancellation API Test",
            description="Testing execution cancellation API.",
        )

        execution_id = f"api-cancel-{uuid4()}"

        started = task_service.start_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert started.status == "running"
        assert started.execution_id == execution_id
        assert started.lease_owner_id == execution_id

        return task.id, execution_id


def test_cancel_execution_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/executions/unauthenticated-execution/cancel"
        )

    assert response.status_code == 401


def test_cancel_execution_unknown_execution_returns_404() -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="execution-cancel-unknown",
        )

        response = client.post(
            "/executions/unknown-execution-id/cancel",
            headers=_auth_headers(token),
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Execution not found."


def test_cancel_execution_foreign_user_returns_404() -> None:
    with TestClient(app) as client:
        owner_token, owner_id = _register_and_login(
            client,
            prefix="execution-cancel-owner",
        )

        attacker_token, _ = _register_and_login(
            client,
            prefix="execution-cancel-attacker",
        )

        task_id, execution_id = _create_running_task(owner_id)

        # The runtime execution must exist for the owner.
        service = app.state.ai_execution_service
        execution_system = service._execution_system

        execution_system.start(
            execution_id,
            task_id=task_id,
            total_steps=1,
        )

        response = client.post(
            f"/executions/{execution_id}/cancel",
            headers=_auth_headers(attacker_token),
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Execution not found."

        # The attacker must not be able to cancel the execution.
        observation = execution_system.get_observation(
            execution_id
        )

        assert observation is not None
        assert observation.status == "running"

        # Keep owner token referenced so the ownership scenario
        # remains explicit in the test.
        assert owner_token


def test_cancel_execution_success() -> None:
    with TestClient(app) as client:
        token, user_id = _register_and_login(
            client,
            prefix="execution-cancel-success",
        )

        task_id, execution_id = _create_running_task(user_id)

        service = app.state.ai_execution_service
        execution_system = service._execution_system

        record = execution_system.start(
            execution_id,
            task_id=task_id,
            total_steps=1,
        )

        assert record.status == "running"

        response = client.post(
            f"/executions/{execution_id}/cancel",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload["execution_id"] == execution_id
        assert payload["task_id"] == task_id
        assert payload["status"] == "cancelled"
        assert payload["message"] == (
            "Execution cancelled successfully."
        )

        with session_scope() as session:
            task = TaskRepository(session).get_by_id(task_id)

            assert task is not None
            assert task.status == "cancelled"
            assert task.execution_id == execution_id
            assert task.lease_owner_id is None
            assert task.lease_expires_at is None
            assert task.last_heartbeat_at is None


def test_cancel_execution_updates_runtime_observation() -> None:
    with TestClient(app) as client:
        token, user_id = _register_and_login(
            client,
            prefix="execution-cancel-observation",
        )

        task_id, execution_id = _create_running_task(user_id)

        service = app.state.ai_execution_service
        execution_system = service._execution_system

        execution_system.start(
            execution_id,
            task_id=task_id,
            total_steps=1,
        )

        response = client.post(
            f"/executions/{execution_id}/cancel",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200

        observation = execution_system.get_observation(
            execution_id
        )

        assert observation is not None
        assert observation.status == "cancelled"


def test_cancel_execution_creates_audit_event() -> None:
    with TestClient(app) as client:
        token, user_id = _register_and_login(
            client,
            prefix="execution-cancel-audit",
        )

        task_id, execution_id = _create_running_task(user_id)

        service = app.state.ai_execution_service
        execution_system = service._execution_system

        execution_system.start(
            execution_id,
            task_id=task_id,
            total_steps=1,
        )

        response = client.post(
            f"/executions/{execution_id}/cancel",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200

        audit = execution_system.get_audit(
            execution_id
        )

        assert any(
            event.event_type == "execution.cancelled"
            for event in audit
        )


def test_cancel_execution_clears_runtime_registration() -> None:
    with TestClient(app) as client:
        token, user_id = _register_and_login(
            client,
            prefix="execution-cancel-registration",
        )

        task_id, execution_id = _create_running_task(user_id)

        service = app.state.ai_execution_service
        execution_system = service._execution_system

        execution_system.start(
            execution_id,
            task_id=task_id,
            total_steps=1,
        )

        assert execution_system.is_registered(
            execution_id
        )

        response = client.post(
            f"/executions/{execution_id}/cancel",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200

        assert not execution_system.is_registered(
            execution_id
        )