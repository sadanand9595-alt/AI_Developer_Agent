"""
Integration tests for Agent execution API.

These tests verify the HTTP boundary, authentication, Agent lookup,
Task creation/lifecycle, and delegation into the autonomous AI
execution pipeline.

The database and FastAPI application are real. AI execution itself
is patched only to make the HTTP tests deterministic and independent
of a live model response.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from database.repositories.task_repository import TaskRepository
from database.session import session_scope
from services.agent_service import AgentService
from services.ai_execution_service import AIExecutionService
from core.pipeline_context import PipelineContext
from core.result import Result


@pytest.fixture()
def client() -> TestClient:
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
