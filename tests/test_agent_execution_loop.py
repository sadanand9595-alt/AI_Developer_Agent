from __future__ import annotations
from uuid import uuid4

import json
from types import SimpleNamespace
from typing import Any

from ai.planner import AIPlanner
from ai.provider import AIProvider
from core.action_executor import ActionExecutor
from core.action_registry import ActionRegistry
from core.execution_system_factory import ExecutionSystemFactory
from core.pipeline_context import PipelineContext
from core.planner import PlanStep
from core.result import Result
from services.ai_execution_service import AIExecutionService


class LoopProvider(AIProvider):
    def generate(self, prompt: str) -> Result[str]:
        if prompt.startswith("You are the planning"):
            return Result.ok(
                '[{"name":"generate","description":"Generate code",'
                '"action":"generate_code","requires_approval":false,'
                '"metadata":{"objective_complete":true}}]'
            )
        return Result.ok("generated")


class FailingProvider(AIProvider):
    def generate(self, prompt: str) -> Result[str]:
        if prompt.startswith("You are the planning"):
            return Result.ok(
                '[{"name":"generate","description":"Generate code",'
                '"action":"generate_code","requires_approval":false,'
                '"metadata":{}}]'
            )
        return Result.fail("PROVIDER_FAILURE", "Provider failed.")


def _service(provider: AIProvider) -> AIExecutionService:
    return AIExecutionService(
        AIPlanner(provider),
        ExecutionSystemFactory.create_with_provider(provider),
    )


def test_agent_stops_after_successful_objective() -> None:
    result = _service(LoopProvider()).execute_agent("build it")
    assert result.is_success()
    context = result.require_data()
    assert context.get_metadata("iteration") == 1
    assert context.get_metadata("execution_status") == "completed"


def test_agent_stops_at_iteration_limit() -> None:
    class IncompleteProvider(LoopProvider):
        def generate(self, prompt: str) -> Result[str]:
            if prompt.startswith("You are the planning"):
                return Result.ok(
                    '[{"name":"generate","description":"Generate code",'
                    '"action":"generate_code","requires_approval":false,'
                    '"metadata":{"objective_complete":false}}]'
                )
            return Result.ok("generated")

    result = _service(IncompleteProvider()).execute_agent(
        "build it",
        max_iterations=2,
    )
    assert result.is_failure()
    assert result.error.code == "AGENT_ITERATION_LIMIT"


def test_agent_replans_until_objective_is_complete() -> None:
    class ReplanningProvider(LoopProvider):
        calls = 0

        def generate(self, prompt: str) -> Result[str]:
            if prompt.startswith("You are the planning"):
                self.calls += 1
                complete = self.calls == 2
                return Result.ok(json.dumps([{
                    "name": "generate",
                    "description": "Generate code",
                    "action": "generate_code",
                    "requires_approval": False,
                    "metadata": {"objective_complete": complete},
                }]))
            return Result.ok("generated")

    result = _service(ReplanningProvider()).execute_agent("build it")
    assert result.is_success()
    context = result.require_data()
    assert context.get_metadata("iteration") == 2
    assert len(context.get_metadata("plan_ids", [])) == 2


def test_agent_preserves_planner_and_action_failures() -> None:
    result = _service(FailingProvider()).execute_agent("build it")
    assert result.is_failure()
    assert result.error.code == "PROVIDER_FAILURE"


def test_agent_honors_cancellation_before_planning() -> None:
    context = PipelineContext()
    context.set_metadata("cancel_requested", True)
    result = _service(LoopProvider()).execute_agent(
        "build it",
        context=context,
    )
    assert result.is_failure()
    assert result.error.code == "EXECUTION_CANCELLED"
    assert context.get_metadata("execution_status") == "cancelled"


def test_action_executor_stops_for_approval() -> None:
    registry = ActionRegistry()
    called: list[Any] = []

    def action(context: PipelineContext) -> Result[str]:
        called.append(context)
        return Result.ok("should not run")

    assert registry.register("restricted", action).is_success()
    result = ActionExecutor(registry).execute_step(
        PlanStep(
            step_id="step-1",
            name="restricted",
            description="Restricted action",
            action="restricted",
            order=1,
            requires_approval=True,
        ),
        PipelineContext(),
    )
    assert result.is_failure()
    assert result.error.code == "APPROVAL_REQUIRED"
    assert not called


def test_approval_is_persisted_and_resume_uses_same_execution() -> None:
    class ApprovalStore:
        def __init__(self) -> None:
            self.approval = None

        def request_approval(self, **kwargs: object) -> SimpleNamespace:
            self.approval = SimpleNamespace(
                id="approval-1",
                status="pending",
                execution_id=kwargs["execution_id"],
                request_payload=kwargs["request_payload"],
            )
            return self.approval

        def get_approval(self, approval_id: str) -> SimpleNamespace | None:
            return self.approval if approval_id == "approval-1" else None

    class ApprovalProvider(LoopProvider):
        def generate(self, prompt: str) -> Result[str]:
            if prompt.startswith("You are the planning"):
                return Result.ok(
                    '[{"name":"generate","description":"Generate code",'
                    '"action":"generate_code","requires_approval":true,'
                    '"metadata":{"objective_complete":true}}]'
                )
            return Result.ok("generated")

    store = ApprovalStore()
    service = _service(ApprovalProvider())
    context = PipelineContext(user_id="user-1")
    paused = service.execute(
        "build it",
        context=context,
        approval_service=store,
    )
    assert paused.is_failure()
    assert paused.error.code == "APPROVAL_REQUIRED"
    assert paused.error.details["execution_id"] == context.execution_id
    assert service._execution_system.get(context.execution_id).status == (
        "waiting_approval"
    )

    store.approval.status = "approved"
    resumed = service.resume_approved_execution(
        context.execution_id,
        "approval-1",
        approval_service=store,
    )
    assert resumed.is_success()
    assert resumed.require_data().execution_id == context.execution_id


def test_approval_resume_recovers_after_coordinator_restart() -> None:
    store = SimpleNamespace()

    def request_approval(**kwargs: object) -> SimpleNamespace:
        store.approval = SimpleNamespace(
            id="approval-restart",
            status="pending",
            execution_id=kwargs["execution_id"],
            request_payload=kwargs["request_payload"],
        )
        return store.approval

    def get_approval(approval_id: str) -> SimpleNamespace | None:
        return (
            store.approval
            if approval_id == "approval-restart"
            else None
        )

    store.request_approval = request_approval
    store.get_approval = get_approval
    class ApprovalProvider(LoopProvider):
        def generate(self, prompt: str) -> Result[str]:
            if prompt.startswith("You are the planning"):
                return Result.ok(
                    '[{"name":"generate","description":"Generate code",'
                    '"action":"generate_code","requires_approval":true,'
                    '"metadata":{"objective_complete":true}}]'
                )
            return Result.ok("generated")

    provider = ApprovalProvider()
    first_service = _service(provider)
    context = PipelineContext(user_id="user-1")
    paused = first_service.execute(
        "build it",
        context=context,
        approval_service=store,
    )
    assert paused.error.code == "APPROVAL_REQUIRED"

    store.approval.status = "approved"
    restarted_service = _service(provider)
    resumed = restarted_service.resume_approved_execution(
        context.execution_id,
        "approval-restart",
        approval_service=store,
    )
    assert resumed.is_success()
    assert resumed.require_data().execution_id == context.execution_id

def test_approval_updates_durable_task_lifecycle() -> None:
    from database.repositories.user_repository import UserRepository
    from database.session import session_scope
    from core.types import TaskStatus
    from services.task_service import TaskService

    class ApprovalStore:
        def __init__(self) -> None:
            self.approval = None

        def request_approval(self, **kwargs: object) -> SimpleNamespace:
            self.approval = SimpleNamespace(
                id="approval-durable-1",
                status="pending",
                execution_id=kwargs["execution_id"],
                request_payload=kwargs["request_payload"],
            )
            return self.approval

        def get_approval(
            self,
            approval_id: str,
        ) -> SimpleNamespace | None:
            return (
                self.approval
                if approval_id == "approval-durable-1"
                else None
            )

    class ApprovalProvider(LoopProvider):
        def generate(self, prompt: str) -> Result[str]:
            if prompt.startswith("You are the planning"):
                return Result.ok(
                    '[{"name":"generate","description":"Generate code",'
                    '"action":"generate_code","requires_approval":true,'
                    '"metadata":{"objective_complete":true}}]'
                )
            return Result.ok("generated")

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-ai-{uuid4().hex}@example.com",
            name="Phase 7.3 AI Integration Test User",
            password_hash="phase73-password",
        )

        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user.id,
            title="Durable Approval Execution",
            description="Testing AI approval integration.",
        )

        execution_id = f"phase73-ai-execution-{uuid4().hex}"

        task_service.start_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        context = PipelineContext(
            execution_id=execution_id,
            task_id=task.id,
            user_id=user.id,
        )

        store = ApprovalStore()
        service = _service(ApprovalProvider())

        paused = service.execute(
            "build it",
            context=context,
            approval_service=store,
            task_service=task_service,
        )

        assert paused.is_failure()
        assert paused.error.code == "APPROVAL_REQUIRED"

        refreshed = task_service.get_task(task.id)

        assert refreshed is not None
        assert refreshed.execution_id == execution_id
        assert refreshed.status == TaskStatus.WAITING_APPROVAL.value
        assert refreshed.lease_owner_id is None

        store.approval.status = "approved"

        resumed = service.resume_approved_execution(
            execution_id,
            "approval-durable-1",
            approval_service=store,
            task_service=task_service,
        )

        assert resumed.is_success()
        assert resumed.require_data().execution_id == execution_id

        refreshed = task_service.get_task(task.id)

        assert refreshed is not None
        assert refreshed.execution_id == execution_id
        assert refreshed.status == TaskStatus.RUNNING.value
        assert refreshed.lease_owner_id == execution_id



