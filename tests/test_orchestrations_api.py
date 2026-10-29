from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from api.app import app
from api.deps import get_agent_ai_execution_service
from core.result import Result
from database.session import session_scope
from services.task_service import TaskService


class FakeAgentAIExecutionService:
    def __init__(self, fail_agent_id: str | None = None):
        self.calls = []
        self.fail_agent_id = fail_agent_id

    def execute(self, *, agent_id, request, context):
        self.calls.append(
            {
                "agent_id": agent_id,
                "request": request,
                "context": context,
            }
        )

        if agent_id == self.fail_agent_id:
            return Result.fail(
                "SPECIALIST_FAILURE",
                f"{agent_id} failed as expected.",
            )

        context.output_data = f"{agent_id} processed: {request}"
        return Result.ok(context)


def register_and_login(client: TestClient) -> str:
    email = f"orchestration-api-{uuid4()}@example.com"
    password = "correct-horse-battery"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "Orchestration API Test",
            "password": password,
        },
    )
    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text

    return login_response.json()["access_token"]


def test_sequential_orchestration_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            "/orchestrations/sequential",
            json={
                "request": "Test workflow",
                "specialists": [{"agent_id": "specialist-1"}],
            },
        )

    assert response.status_code == 401


def test_sequential_orchestration_rejects_invalid_payload():
    with TestClient(app) as client:
        token = register_and_login(client)
        response = client.post(
            "/orchestrations/sequential",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "request": "",
                "specialists": [],
            },
        )

    assert response.status_code == 422


def test_sequential_orchestration_executes_specialists_in_order():
    fake_service = FakeAgentAIExecutionService()
    app.dependency_overrides[get_agent_ai_execution_service] = (
        lambda: fake_service
    )

    try:
        with TestClient(app) as client:
            token = register_and_login(client)
            response = client.post(
                "/orchestrations/sequential",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "request": "Start the workflow",
                    "title": "Integration Test Workflow",
                    "specialists": [
                        {
                            "agent_id": "specialist-1",
                            "name": "First Specialist",
                        },
                        {
                            "agent_id": "specialist-2",
                            "name": "Second Specialist",
                        },
                    ],
                },
            )

        assert response.status_code == 200, response.text
        data = response.json()

        assert data["status"] == "completed"
        assert data["successful_count"] == 2
        assert data["failed_count"] == 0
        assert data["partial_result"] is False
        assert data["task_id"]
        assert data["execution_id"]

        assert [call["agent_id"] for call in fake_service.calls] == [
            "specialist-1",
            "specialist-2",
        ]
        assert "Previous specialist output:" in fake_service.calls[1]["request"]
        assert fake_service.calls[0]["context"].output_data in (
            fake_service.calls[1]["request"]
        )

        with session_scope() as session:
            task = TaskService(session).get_task(data["task_id"])
            assert task is not None
            assert task.status == "completed"
            assert task.result_json is not None
            assert task.result_json["status"] == "completed"
    finally:
        app.dependency_overrides.pop(
            get_agent_ai_execution_service,
            None,
        )


def test_sequential_orchestration_returns_partial_result_on_failure():
    fake_service = FakeAgentAIExecutionService(
        fail_agent_id="specialist-2",
    )
    app.dependency_overrides[get_agent_ai_execution_service] = (
        lambda: fake_service
    )

    try:
        with TestClient(app) as client:
            token = register_and_login(client)
            response = client.post(
                "/orchestrations/sequential",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "request": "Run workflow with a failure",
                    "specialists": [
                        {"agent_id": "specialist-1"},
                        {"agent_id": "specialist-2"},
                        {"agent_id": "specialist-3"},
                    ],
                },
            )

        assert response.status_code == 200, response.text
        data = response.json()

        assert data["status"] == "completed"
        assert data["partial_result"] is True
        assert data["successful_count"] == 2
        assert data["failed_count"] == 1
        assert [call["agent_id"] for call in fake_service.calls] == [
            "specialist-1",
            "specialist-2",
            "specialist-3",
        ]
    finally:
        app.dependency_overrides.pop(
            get_agent_ai_execution_service,
            None,
        )
