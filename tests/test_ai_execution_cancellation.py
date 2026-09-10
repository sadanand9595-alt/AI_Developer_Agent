from ai.planner import AIPlanner
from ai.provider import AIProvider
from core.execution_system_factory import ExecutionSystemFactory
from core.result import Result
from services.ai_execution_service import AIExecutionService


class StubProvider(AIProvider):
    def generate(self, prompt: str) -> Result[str]:
        return Result.ok("print(42)")


def test_ai_execution_service_cancel_execution() -> None:
    provider = StubProvider()

    service = AIExecutionService(
        AIPlanner(provider),
        ExecutionSystemFactory.create_with_provider(provider),
    )

    execution_system = service._execution_system

    record = execution_system.start(
        "service-cancel-execution-001",
        task_id="service-cancel-task-001",
        total_steps=1,
    )

    assert record.status == "running"
    assert execution_system.is_registered(
        "service-cancel-execution-001"
    )

    result = service.cancel_execution(
        "service-cancel-execution-001"
    )

    assert result.is_failure()
    assert result.error.code == "EXECUTION_CANCELLED"

    cancelled = execution_system.get(
        "service-cancel-execution-001"
    )

    assert cancelled is not None
    assert cancelled.status == "cancelled"

    assert not execution_system.is_registered(
        "service-cancel-execution-001"
    )

    observation = execution_system.get_observation(
        "service-cancel-execution-001"
    )

    assert observation is not None
    assert observation.status == "cancelled"

    audit = execution_system.get_audit(
        "service-cancel-execution-001"
    )

    assert any(
        item.event_type == "execution.cancelled"
        for item in audit
    )

    execution_system.close()