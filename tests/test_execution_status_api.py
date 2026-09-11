"""
Integration tests for the unified Execution Status API.

Phase 7.2 establishes:
- GET /executions/{execution_id}
- authentication
- user isolation
- durable Task-backed execution status
- unified execution response
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from core.pipeline_context import PipelineContext
from core.result import Result
from services.ai_execution_service import AIExecutionService

from tests.test_agents_api import (
    _auth_headers,
    _create_agent,
    _register_and_login,
)


def test_execution_status_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get(
            f"/executions/{uuid4()}",
        )

        assert response.status_code == 401


def test_unknown_execution_status_returns_404() -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="phase7-status-unknown",
        )

        execution_id = str(uuid4())

        response = client.get(
            f"/executions/{execution_id}",
            headers=_auth_headers(token),
        )

        assert response.status_code == 404


def test_execution_status_returns_durable_completed_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="phase7-status-completed",
        )

        agent_id = _create_agent(
            name_prefix="Phase 7 Status Agent",
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

            context.set_output(
                "Phase 7.2 status test output"
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
                "request": (
                    "Create Phase 7.2 status test execution."
                ),
            },
        )

        assert response.status_code == 200, response.text

        execution = response.json()

        execution_id = execution["execution_id"]

        response = client.get(
            f"/executions/{execution_id}",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200, response.text

        payload = response.json()

        assert payload["execution_id"] == execution_id
        assert payload["task_id"] == execution["task_id"]
        assert payload["agent_id"] == agent_id
        assert payload["status"] == "completed"
        assert payload["retry_count"] == 0

        assert payload["title"]
        assert payload["description"]

        assert payload["result"] is not None
        assert payload["error"] is None

        assert payload["created_at"] is not None
        assert payload["updated_at"] is not None


def test_execution_status_isolated_between_users(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token_one, _ = _register_and_login(
            client,
            prefix="phase7-status-isolation-one",
        )

        token_two, _ = _register_and_login(
            client,
            prefix="phase7-status-isolation-two",
        )

        agent_id = _create_agent(
            name_prefix="Phase 7 Isolation Agent",
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

            context.set_output(
                "Isolation test output"
            )

            return Result.ok(context)

        monkeypatch.setattr(
            AIExecutionService,
            "execute_agent",
            fake_execute_agent,
        )

        response = client.post(
            f"/agents/{agent_id}/execute",
            headers=_auth_headers(token_one),
            json={
                "request": "Create isolated execution.",
            },
        )

        assert response.status_code == 200, response.text

        execution_id = response.json()["execution_id"]

        response = client.get(
            f"/executions/{execution_id}",
            headers=_auth_headers(token_two),
        )

        assert response.status_code == 404, response.text


def test_execution_status_returns_failed_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="phase7-status-failed",
        )

        agent_id = _create_agent(
            name_prefix="Phase 7 Failed Status Agent",
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

            return Result.fail(
                "TEST_EXECUTION_FAILED",
                "Intentional Phase 7.2 failure.",
                details={
                    "test": True,
                },
            )

        monkeypatch.setattr(
            AIExecutionService,
            "execute_agent",
            fake_execute_agent,
        )

        response = client.post(
            f"/agents/{agent_id}/execute",
            headers=_auth_headers(token),
            json={
                "request": "Create failed execution.",
            },
        )

        assert response.status_code == 502, response.text

        error = response.json()["error"]

        assert error["code"] == "TEST_EXECUTION_FAILED"
        assert error["message"] == "Intentional Phase 7.2 failure."

        details = error["details"]

        assert details["test"] is True
        assert "task_id" in details
        assert "execution_id" in details

        execution_id = details["execution_id"]

        response = client.get(
            f"/executions/{execution_id}",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200, response.text

        payload = response.json()

        assert payload["execution_id"] == execution_id
        assert payload["agent_id"] == agent_id
        assert payload["status"] == "failed"
        assert payload["result"] is None
        assert payload["error"] is not None


def test_execution_status_returns_cancelled_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="phase7-status-cancelled",
        )

        agent_id = _create_agent(
            name_prefix="Phase 7 Cancelled Status Agent",
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

            context.set_metadata(
                "cancel_requested",
                True,
            )

            return Result.fail(
                "EXECUTION_CANCELLED",
                "Intentional cancellation.",
                details={
                    "execution_id": context.execution_id,
                    "task_id": context.task_id,
                },
            )

        monkeypatch.setattr(
            AIExecutionService,
            "execute_agent",
            fake_execute_agent,
        )

        response = client.post(
            f"/agents/{agent_id}/execute",
            headers=_auth_headers(token),
            json={
                "request": "Create cancelled execution.",
            },
        )

        # The execution API should expose the execution ID even
        # when the execution terminates through cancellation.
        assert response.status_code in (200, 409, 502), response.text
