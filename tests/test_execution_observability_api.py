"""
Integration tests for Execution observability API.

Phase 6.1 establishes the API contract for:
- execution progress
- execution observation
- execution audit
- authentication
- user isolation
- durable Task -> execution ownership
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

from tests.test_agents_api import (
    _auth_headers,
    _create_agent,
    _register_and_login,
)


def _create_completed_agent_execution(
    client: TestClient,
    *,
    token: str,
    agent_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> dict:
    """
    Create a durable completed Agent execution.

    This uses the existing Agent execution API boundary so the
    observability tests do not bypass Task ownership.
    """

    from services.ai_execution_service import AIExecutionService

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
            "Phase 6 observability test output"
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
            "request": "Create observability test execution.",
        },
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["execution_id"]
    assert payload["task_id"]
    assert payload["agent_id"] == agent_id
    assert payload["status"] == TaskStatus.COMPLETED.value

    return payload


def _create_live_execution_observability(
    execution_id: str,
    task_id: str,
) -> None:
    """
    Register deterministic live observability data in the existing
    ExecutionSystem.

    This helper is intentionally isolated from the API implementation.
    """

    execution_system = app.state.ai_execution_service._execution_system

    execution_system.start(
        execution_id,
        task_id=task_id,
        total_steps=2,
        metadata={
            "phase": "6.1",
            "test": True,
        },
    )

    execution_system.start_step(
        execution_id,
        "step_one",
    )

    execution_system.complete_step(
        execution_id,
        "step_one",
    )

    execution_system.start_step(
        execution_id,
        "step_two",
    )

    execution_system.complete_step(
        execution_id,
        "step_two",
    )


def test_execution_progress_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get(
            f"/executions/{uuid4()}/progress",
        )

        assert response.status_code == 401


def test_execution_observation_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get(
            f"/executions/{uuid4()}/observation",
        )

        assert response.status_code == 401


def test_execution_audit_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get(
            f"/executions/{uuid4()}/audit",
        )

        assert response.status_code == 401


def test_execution_progress_returns_live_progress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, user_id = _register_and_login(
            client,
            prefix="phase6-progress",
        )

        agent_id = _create_agent(
            name_prefix="Phase 6 Progress Agent",
        )

        execution = _create_completed_agent_execution(
            client,
            token=token,
            agent_id=agent_id,
            monkeypatch=monkeypatch,
        )

        execution_id = execution["execution_id"]

        with session_scope() as session:
            task = TaskRepository(session).get_by_execution_id_and_user(
                execution_id,
                user_id,
            )

            assert task is not None

            _create_live_execution_observability(
                execution_id,
                task.id,
            )

        response = client.get(
            f"/executions/{execution_id}/progress",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200, response.text

        payload = response.json()

        assert payload["execution_id"] == execution_id
        assert payload["task_id"] == execution["task_id"]
        assert payload["total_steps"] == 2
        assert payload["completed_steps"] == 2
        assert payload["progress_percent"] == 100.0


def test_execution_observation_returns_live_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, user_id = _register_and_login(
            client,
            prefix="phase6-observation",
        )

        agent_id = _create_agent(
            name_prefix="Phase 6 Observation Agent",
        )

        execution = _create_completed_agent_execution(
            client,
            token=token,
            agent_id=agent_id,
            monkeypatch=monkeypatch,
        )

        execution_id = execution["execution_id"]

        with session_scope() as session:
            task = TaskRepository(session).get_by_execution_id_and_user(
                execution_id,
                user_id,
            )

            assert task is not None

            _create_live_execution_observability(
                execution_id,
                task.id,
            )

        response = client.get(
            f"/executions/{execution_id}/observation",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200, response.text

        payload = response.json()

        assert payload["execution_id"] == execution_id
        assert payload["task_id"] == execution["task_id"]
        assert payload["total_steps"] == 2
        assert payload["completed_steps"] == 2
        assert payload["progress_percent"] == 100.0
        assert payload["events_received"] >= 1


def test_execution_audit_returns_execution_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, user_id = _register_and_login(
            client,
            prefix="phase6-audit",
        )

        agent_id = _create_agent(
            name_prefix="Phase 6 Audit Agent",
        )

        execution = _create_completed_agent_execution(
            client,
            token=token,
            agent_id=agent_id,
            monkeypatch=monkeypatch,
        )

        execution_id = execution["execution_id"]

        with session_scope() as session:
            task = TaskRepository(session).get_by_execution_id_and_user(
                execution_id,
                user_id,
            )

            assert task is not None

            _create_live_execution_observability(
                execution_id,
                task.id,
            )

        response = client.get(
            f"/executions/{execution_id}/audit",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200, response.text

        payload = response.json()

        assert payload["execution_id"] == execution_id
        assert isinstance(payload["events"], list)
        assert len(payload["events"]) >= 1

        event_execution_ids = {
            event["execution_id"]
            for event in payload["events"]
        }

        assert event_execution_ids == {execution_id}


def test_execution_observability_isolated_between_users(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token_one, user_one_id = _register_and_login(
            client,
            prefix="phase6-isolation-one",
        )

        token_two, _ = _register_and_login(
            client,
            prefix="phase6-isolation-two",
        )

        agent_id = _create_agent(
            name_prefix="Phase 6 Isolation Agent",
        )

        execution = _create_completed_agent_execution(
            client,
            token=token_one,
            agent_id=agent_id,
            monkeypatch=monkeypatch,
        )

        execution_id = execution["execution_id"]

        with session_scope() as session:
            task = TaskRepository(session).get_by_execution_id_and_user(
                execution_id,
                user_one_id,
            )

            assert task is not None

            _create_live_execution_observability(
                execution_id,
                task.id,
            )

        for suffix in (
            "progress",
            "observation",
            "audit",
        ):
            response = client.get(
                f"/executions/{execution_id}/{suffix}",
                headers=_auth_headers(token_two),
            )

            assert response.status_code == 404, (
                suffix,
                response.text,
            )


def test_unknown_execution_returns_404() -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="phase6-unknown",
        )

        execution_id = str(uuid4())

        for suffix in (
            "progress",
            "observation",
            "audit",
        ):
            response = client.get(
                f"/executions/{execution_id}/{suffix}",
                headers=_auth_headers(token),
            )

            assert response.status_code == 404, (
                suffix,
                response.text,
            )


def test_execution_observability_requires_durable_task_ownership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_login(
            client,
            prefix="phase6-no-task",
        )

        execution_id = str(uuid4())

        execution_system = app.state.ai_execution_service._execution_system

        execution_system.start(
            execution_id,
            task_id=str(uuid4()),
            total_steps=1,
        )

        response = client.get(
            f"/executions/{execution_id}/progress",
            headers=_auth_headers(token),
        )

        assert response.status_code == 404

