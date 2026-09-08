from unittest.mock import Mock

from ai.planner import AIPlanner
from core.execution_system import ExecutionSystem
from core.pipeline_context import PipelineContext
from core.result import Result
from database.models.agent import Agent
from services.agent_ai_execution_service import AgentAIExecutionService
from services.agent_runtime_service import AgentRuntimeService
from services.ai_execution_service import AIExecutionService


def _build_ai_execution_service():
    planner = Mock(spec=AIPlanner)
    execution_system = Mock(spec=ExecutionSystem)

    return AIExecutionService(
        planner=planner,
        execution_system=execution_system,
    )


def _build_agent_runtime_service(agent):
    repository = Mock()
    repository.get_by_id.return_value = agent

    service = AgentRuntimeService.__new__(
        AgentRuntimeService
    )

    service._repository = repository
    service._runtime_manager = Mock()

    return service


def _build_pipeline_context():
    return PipelineContext(
        user_id="test-user",
        task_id="test-task",
        agent_id="agent-001",
    )


def test_agent_ai_execution_service_delegates_to_agent_pipeline():
    agent = Agent(
        id="agent-001",
        name="Test Agent",
        description="Integration test agent",
        agent_type="autonomous",
        model_provider="ollama",
        model_name="qwen2.5-coder:7b",
        capabilities=["code_generation"],
        configuration={"workspace": "test"},
        max_iterations=7,
        is_enabled=True,
    )

    ai_execution_service = _build_ai_execution_service()

    def execute_agent(
        request,
        *,
        context,
        max_iterations,
        approval_service=None,
    ):
        context.set_output(
            {"status": "completed"}
        )

        return Result.ok(context)

    ai_execution_service.execute_agent = Mock(
        side_effect=execute_agent
    )

    agent_runtime_service = _build_agent_runtime_service(
        agent
    )

    runtime = Mock()
    runtime.status.value = "idle"

    agent_runtime_service._runtime_manager.get_or_create.return_value = (
        Result.ok(runtime)
    )

    def execute(*, context, operation):
        operation_result = operation(context)

        return type(
            "RuntimeExecution",
            (),
            {
                "status": runtime.status,
                "result": operation_result,
            },
        )()

    runtime.execute.side_effect = execute

    service = AgentAIExecutionService(
        ai_execution_service=ai_execution_service,
        agent_runtime_service=agent_runtime_service,
    )

    input_context = _build_pipeline_context()

    result = service.execute(
        agent_id="agent-001",
        request="Create a test Python agent.",
        context=input_context,
    )

    assert result.is_success()

    final_context = result.require_data()

    assert final_context is input_context

    assert final_context.get_metadata("agent_id") == "agent-001"
    assert final_context.get_metadata("agent_type") == "autonomous"
    assert final_context.get_metadata("model_provider") == "ollama"
    assert final_context.get_metadata("model_name") == "qwen2.5-coder:7b"
    assert final_context.get_metadata("capabilities") == [
        "code_generation"
    ]
    assert final_context.get_metadata("agent_configuration") == {
        "workspace": "test"
    }
    assert final_context.get_metadata("max_iterations") == 7
    assert final_context.get_metadata("agent_execution") is True

    assert final_context.input_data == (
        "Create a test Python agent."
    )

    assert final_context.output_data == {
        "status": "completed"
    }

    ai_execution_service.execute_agent.assert_called_once()

    call = ai_execution_service.execute_agent.call_args

    assert call.args[0] == (
        "Create a test Python agent."
    )

    assert call.kwargs["context"] is input_context
    assert call.kwargs["max_iterations"] == 7

    runtime.execute.assert_called_once()


def test_agent_ai_execution_service_rejects_unknown_agent():
    ai_execution_service = _build_ai_execution_service()
    ai_execution_service.execute_agent = Mock()

    agent_runtime_service = AgentRuntimeService.__new__(
        AgentRuntimeService
    )

    repository = Mock()
    repository.get_by_id.return_value = None

    agent_runtime_service._repository = repository
    agent_runtime_service._runtime_manager = Mock()

    service = AgentAIExecutionService(
        ai_execution_service=ai_execution_service,
        agent_runtime_service=agent_runtime_service,
    )

    result = service.execute(
        agent_id="missing-agent",
        request="Do something.",
    )

    assert result.is_failure()
    assert result.error.code == "AGENT_NOT_FOUND"

    ai_execution_service.execute_agent.assert_not_called()

    agent_runtime_service._runtime_manager.get_or_create.assert_not_called()


def test_agent_ai_execution_service_rejects_disabled_agent():
    agent = Agent(
        id="disabled-agent",
        name="Disabled Agent",
        description="Disabled test agent",
        agent_type="autonomous",
        model_provider="ollama",
        model_name="qwen2.5-coder:7b",
        max_iterations=7,
        is_enabled=False,
    )

    ai_execution_service = _build_ai_execution_service()
    ai_execution_service.execute_agent = Mock()

    agent_runtime_service = _build_agent_runtime_service(
        agent
    )

    service = AgentAIExecutionService(
        ai_execution_service=ai_execution_service,
        agent_runtime_service=agent_runtime_service,
    )

    result = service.execute(
        agent_id="disabled-agent",
        request="Do something.",
    )

    assert result.is_failure()
    assert result.error.code == "AGENT_DISABLED"

    ai_execution_service.execute_agent.assert_not_called()

    agent_runtime_service._runtime_manager.get_or_create.assert_not_called()
