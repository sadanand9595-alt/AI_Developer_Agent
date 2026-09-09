"""
Integration tests for Agent execution history API.

These tests verify durable Agent execution history, authentication,
user isolation, Agent scoping, and Task-to-Agent linkage.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from core.pipeline_context import PipelineContext
from core.result import Result
from database.models.task import TaskStatus
from database.repositories.task_repository import TaskRepository
from database.session import session_scope
from services.ai_execution_service import AIExecutionService

from tests.test_agents_api import (
    _auth_headers,
    _create_agent,
    _register_and_login,
)


def _execute_agent(
    client: TestClient,
    *,
    token: str,
    agent_id: str,
    request: str,
    monkeypatch: pytest.MonkeyPatch,
) -> dict:
    """Execute an Agent through the real API boundary."""

    def fake_execute_agent(
        self: AIExecutionService,
        request: str,
        *,
        context: PipelineContext | None = None,
        max_iterations: int | None = None,
        approval_service=None,
    ) -> Result[PipelineContext]:
        assert context is not None
        assert context.agent_id == agent_id
        assert context.task_id is not None

        context.set_output(
            "History API test output"
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
        headers=_auth_headers(token),
        json={
            "request": request,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


def test_agent_execution_history_requires_authentication() -> None:
    with TestClient(app) as client:
        agent_id = _create_agent()

        response = client.get(
            f"/agents/{agent_id}/executions",
        )

        assert response.status_code == 401


def test_agent_execution_history_lists_completed_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="history-list",
        )

        agent_id = _create_agent(
            name_prefix="History List Agent",
        )

        execution = _execute_agent(
            client,
            token=token,
            agent_id=agent_id,
            request="Create an execution history entry.",
            monkeypatch=monkeypatch,
        )

        response = client.get(
            f"/agents/{agent_id}/executions",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200, response.text

        executions = response.json()

        matching = [
            item
            for item in executions
            if item["execution_id"] == execution["execution_id"]
        ]

        assert len(matching) == 1

        item = matching[0]

        assert item["task_id"] == execution["task_id"]
        assert item["agent_id"] == agent_id
        assert item["status"] == "completed"
        assert item["result"] is not None
        assert item["error"] is None


def test_agent_execution_history_detail_returns_exact_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="history-detail",
        )

        agent_id = _create_agent(
            name_prefix="History Detail Agent",
        )

        execution = _execute_agent(
            client,
            token=token,
            agent_id=agent_id,
            request="Create an execution detail entry.",
            monkeypatch=monkeypatch,
        )

        execution_id = execution["execution_id"]

        response = client.get(
            f"/agents/{agent_id}/executions/{execution_id}",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200, response.text

        item = response.json()

        assert item["execution_id"] == execution_id
        assert item["task_id"] == execution["task_id"]
        assert item["agent_id"] == agent_id
        assert item["status"] == "completed"
        assert item["result"] is not None
        assert item["error"] is None


def test_agent_execution_history_isolated_between_users(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token_one, _ = _register_and_login(
            client,
            prefix="history-user-one",
        )

        token_two, _ = _register_and_login(
            client,
            prefix="history-user-two",
        )

        agent_id = _create_agent(
            name_prefix="History Isolation Agent",
        )

        execution = _execute_agent(
            client,
            token=token_one,
            agent_id=agent_id,
            request="Private execution for user one.",
            monkeypatch=monkeypatch,
        )

        list_response = client.get(
            f"/agents/{agent_id}/executions",
            headers=_auth_headers(token_two),
        )

        assert list_response.status_code == 200, list_response.text

        executions = list_response.json()

        assert all(
            item["execution_id"] != execution["execution_id"]
            for item in executions
        )

        detail_response = client.get(
            f"/agents/{agent_id}/executions/"
            f"{execution['execution_id']}",
            headers=_auth_headers(token_two),
        )

        assert detail_response.status_code == 404


def test_agent_execution_history_unknown_agent_returns_404() -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="history-unknown-agent",
        )

        response = client.get(
            f"/agents/{uuid4()}/executions",
            headers=_auth_headers(token),
        )

        assert response.status_code == 404


def test_agent_execution_history_unknown_execution_returns_404() -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="history-unknown-execution",
        )

        agent_id = _create_agent(
            name_prefix="History Unknown Execution Agent",
        )

        response = client.get(
            f"/agents/{agent_id}/executions/{uuid4()}",
            headers=_auth_headers(token),
        )

        assert response.status_code == 404


def test_agent_execution_history_rejects_wrong_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="history-wrong-agent",
        )

        agent_one_id = _create_agent(
            name_prefix="History Agent One",
        )

        agent_two_id = _create_agent(
            name_prefix="History Agent Two",
        )

        execution = _execute_agent(
            client,
            token=token,
            agent_id=agent_one_id,
            request="Execution belongs to agent one.",
            monkeypatch=monkeypatch,
        )

        response = client.get(
            f"/agents/{agent_two_id}/executions/"
            f"{execution['execution_id']}",
            headers=_auth_headers(token),
        )

        assert response.status_code == 404


def test_agent_execution_task_persists_agent_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="history-agent-link",
        )

        agent_id = _create_agent(
            name_prefix="History Agent Link",
        )

        execution = _execute_agent(
            client,
            token=token,
            agent_id=agent_id,
            request="Verify Agent ID persistence.",
            monkeypatch=monkeypatch,
        )

        with session_scope() as session:
            task = TaskRepository(session).get_by_execution_id(
                execution["execution_id"],
            )

            assert task is not None
            assert task.agent_id == agent_id
            assert task.execution_id == execution["execution_id"]
            assert task.status == TaskStatus.COMPLETED.value
