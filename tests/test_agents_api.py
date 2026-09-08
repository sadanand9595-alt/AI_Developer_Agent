"""
Integration tests for Agent management and execution API.

These tests verify the authenticated HTTP boundary, Agent creation,
listing, lookup, update, lifecycle management, Task creation/lifecycle,
and delegation into the autonomous AI execution pipeline.

The database and FastAPI application are real. AI execution itself
is patched only to make the execution tests deterministic and
independent of a live model response.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from core.pipeline_context import PipelineContext
from core.result import Result
from database.repositories.task_repository import TaskRepository
from database.session import session_scope
from services.agent_service import AgentService
from services.ai_execution_service import AIExecutionService


@pytest.fixture()
def client() -> TestClient:
    """
    Create a lifespan-aware FastAPI test client.

    The application lifespan initializes the AI execution service
    required by the Agent execution dependency.
    """

    with TestClient(app) as test_client:
        yield test_client


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


def _create_agent(
    *,
    name_prefix: str = "API Agent",
    max_iterations: int = 5,
    enabled: bool = True,
):
    """Create a real persistent Agent for the integration test."""

    with session_scope() as session:
        service = AgentService(session)

        agent = service.register_agent(
            name=f"{name_prefix} {uuid4()}",
            agent_type="coding",
            description="Agent API integration test agent.",
            model_provider="local",
            model_name="test-model",
            capabilities=[
                "code_generation",
                "debugging",
                "testing",
            ],
            configuration={
                "test": True,
            },
            max_iterations=max_iterations,
        )

        if not enabled:
            service.disable_agent(agent.id)

        return agent.id


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def test_agent_execute_requires_authentication(
    client: TestClient,
) -> None:
    agent_id = _create_agent()

    response = client.post(
        f"/agents/{agent_id}/execute",
        json={
            "request": "Create a Python hello world program.",
        },
    )

    assert response.status_code == 401


def test_agent_management_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get("/agents")

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Agent Management API
# ---------------------------------------------------------------------------


def test_create_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-create",
    )

    agent_name = f"Created Agent {uuid4()}"

    response = client.post(
        "/agents",
        json={
            "name": agent_name,
            "agent_type": "coding",
            "description": "Created through API.",
            "model_provider": "ollama",
            "model_name": "qwen2.5-coder:7b",
            "capabilities": [
                "code_generation",
            ],
            "configuration": {
                "workspace": "test",
            },
            "max_iterations": 7,
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["name"] == agent_name
    assert body["agent_type"] == "coding"
    assert body["description"] == "Created through API."
    assert body["model_provider"] == "ollama"
    assert body["model_name"] == "qwen2.5-coder:7b"
    assert body["capabilities"] == [
        "code_generation",
    ]
    assert body["configuration"] == {
        "workspace": "test",
    }
    assert body["max_iterations"] == 7
    assert body["is_enabled"] is True
    assert body["status"] == "idle"


def test_create_agent_rejects_blank_name(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-blank-name",
    )

    response = client.post(
        "/agents",
        json={
            "name": "   ",
            "agent_type": "coding",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_create_agent_rejects_invalid_max_iterations(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-invalid-iterations",
    )

    response = client.post(
        "/agents",
        json={
            "name": f"Invalid Iterations Agent {uuid4()}",
            "agent_type": "coding",
            "max_iterations": 0,
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_list_agents(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-list",
    )

    agent_name = f"Listed Agent {uuid4()}"

    _create_agent(
        name_prefix=agent_name,
    )

    response = client.get(
        "/agents",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, list)

    # _create_agent() appends its own UUID to name_prefix,
    # so verify the created Agent by its unique name prefix.
    assert any(
        agent["name"].startswith(agent_name)
        for agent in body
    )


def test_get_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-get",
    )

    agent_id = _create_agent(
        name_prefix="Get API Agent",
    )

    response = client.get(
        f"/agents/{agent_id}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == agent_id
    assert body["agent_type"] == "coding"
    assert body["is_enabled"] is True


def test_get_unknown_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-get-missing",
    )

    response = client.get(
        f"/agents/{uuid4()}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


def test_update_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-update",
    )

    agent_id = _create_agent(
        name_prefix="Update API Agent",
    )

    response = client.patch(
        f"/agents/{agent_id}",
        json={
            "description": "Updated description.",
            "model_name": "updated-model",
            "max_iterations": 12,
            "capabilities": [
                "code_generation",
                "testing",
            ],
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["id"] == agent_id
    assert body["description"] == "Updated description."
    assert body["model_name"] == "updated-model"
    assert body["max_iterations"] == 12
    assert body["capabilities"] == [
        "code_generation",
        "testing",
    ]


def test_update_agent_name(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-update-name",
    )

    agent_id = _create_agent(
        name_prefix="Original Agent",
    )

    new_name = f"Renamed Agent {uuid4()}"

    response = client.patch(
        f"/agents/{agent_id}",
        json={
            "name": new_name,
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == new_name


def test_update_agent_rejects_empty_patch(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-empty-patch",
    )

    agent_id = _create_agent()

    response = client.patch(
        f"/agents/{agent_id}",
        json={},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_update_unknown_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-update-missing",
    )

    response = client.patch(
        f"/agents/{uuid4()}",
        json={
            "description": "Updated.",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 400


def test_enable_and_disable_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-lifecycle",
    )

    agent_id = _create_agent(
        name_prefix="Lifecycle API Agent",
        enabled=False,
    )

    disable_response = client.post(
        f"/agents/{agent_id}/disable",
        headers=_auth_headers(token),
    )

    assert disable_response.status_code == 200

    disabled_body = disable_response.json()

    assert disabled_body["id"] == agent_id
    assert disabled_body["is_enabled"] is False
    assert disabled_body["status"] == "disabled"

    enable_response = client.post(
        f"/agents/{agent_id}/enable",
        headers=_auth_headers(token),
    )

    assert enable_response.status_code == 200

    enabled_body = enable_response.json()

    assert enabled_body["id"] == agent_id
    assert enabled_body["is_enabled"] is True
    assert enabled_body["status"] == "idle"


def test_enable_unknown_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-enable-missing",
    )

    response = client.post(
        f"/agents/{uuid4()}/enable",
        headers=_auth_headers(token),
    )

    assert response.status_code == 400


def test_disable_unknown_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-disable-missing",
    )

    response = client.post(
        f"/agents/{uuid4()}/disable",
        headers=_auth_headers(token),
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Agent Execution API
# ---------------------------------------------------------------------------


def test_agent_execute_rejects_invalid_request(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-invalid-request",
    )

    agent_id = _create_agent()

    response = client.post(
        f"/agents/{agent_id}/execute",
        json={
            "request": "",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_agent_execute_rejects_unknown_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-missing",
    )

    response = client.post(
        f"/agents/{uuid4()}/execute",
        json={
            "request": "Do something.",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


def test_agent_execute_rejects_disabled_agent(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(
        client,
        prefix="agent-disabled",
    )

    agent_id = _create_agent(
        name_prefix="Disabled API Agent",
        enabled=False,
    )

    response = client.post(
        f"/agents/{agent_id}/execute",
        json={
            "request": "Do something.",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 409


def test_agent_execute_success_creates_and_completes_task(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token, user_id = _register_and_login(
        client,
        prefix="agent-success",
    )

    agent_id = _create_agent(
        name_prefix="Success API Agent",
        max_iterations=7,
    )

    def fake_execute_agent(
        self: AIExecutionService,
        request: str,
        *,
        context: PipelineContext | None = None,
        max_iterations: int | None = None,
        approval_service=None,
    ) -> Result[PipelineContext]:
        assert request == "Create a Python hello world program."
        assert context is not None
        assert context.user_id == user_id
        assert context.task_id is not None
        assert context.agent_id == agent_id
        assert max_iterations == 7

        context.set_output(
            "print('Hello from AI Command Center')"
        )

        context.set_metadata(
            "objective_complete",
            True,
        )

        return Result.ok(context)

    monkeypatch.setattr(
        AIExecutionService,
        "execute_agent",
        fake_execute_agent,
    )

    response = client.post(
        f"/agents/{agent_id}/execute",
        json={
            "request": "Create a Python hello world program.",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["agent_id"] == agent_id
    assert body["status"] == "completed"
    assert body["task_id"]
    assert body["execution_id"]
    assert body["output"] == (
        "print('Hello from AI Command Center')"
    )

    task_id = body["task_id"]

    with session_scope() as session:
        task = TaskRepository(session).get_by_id(task_id)

        assert task is not None
        assert task.user_id == user_id
        assert task.status == "completed"
        assert task.execution_id == body["execution_id"]
        assert task.result_json is not None


def test_agent_execute_ai_failure_marks_task_failed(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token, user_id = _register_and_login(
        client,
        prefix="agent-failure",
    )

    agent_id = _create_agent(
        name_prefix="Failure API Agent",
    )

    def fake_execute_agent(
        self: AIExecutionService,
        request: str,
        *,
        context: PipelineContext | None = None,
        max_iterations: int | None = None,
        approval_service=None,
    ) -> Result[PipelineContext]:
        assert context is not None
        assert context.user_id == user_id
        assert context.task_id is not None
        assert context.agent_id == agent_id

        return Result.fail(
            "AI_EXECUTION_FAILED",
            "Simulated AI execution failure.",
        )

    monkeypatch.setattr(
        AIExecutionService,
        "execute_agent",
        fake_execute_agent,
    )

    response = client.post(
        f"/agents/{agent_id}/execute",
        json={
            "request": "This execution should fail.",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 502

    body = response.json()

    assert body["error"]["code"] == "AI_EXECUTION_FAILED"

    task_id = body["error"].get("details", {}).get(
        "task_id"
    )

    if task_id:
        with session_scope() as session:
            task = TaskRepository(session).get_by_id(task_id)

            assert task is not None
            assert task.user_id == user_id
            assert task.status == "failed"