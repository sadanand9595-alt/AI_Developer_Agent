from core.action_registry import ActionRegistry
from core.execution_engine import ExecutionEngine
from core.execution_request import ExecutionRequest
from core.execution_service import ExecutionService
from core.pipeline_context import PipelineContext
from core.result import Result


def main() -> None:
    registry = ActionRegistry()

    def analyze(context: PipelineContext):
        return Result.ok(
            {
                "stage": "analyze",
                "status": "completed",
            }
        )

    def generate_code(context: PipelineContext):
        return Result.ok(
            {
                "stage": "generate_code",
                "status": "completed",
                "files": 5,
            }
        )

    registry.register(
        "analyze_requirements",
        analyze,
    )

    registry.register(
        "generate_code",
        generate_code,
    )

    engine = ExecutionEngine(
        registry
    )

    service = ExecutionService(
        engine
    )

    request = ExecutionRequest.create(
        request="Create a production-ready CRM application.",
        user_id="user-001",
        task_id="task-001",
        agent_id="agent-001",
        session_id="session-001",
        conversation_id="conversation-001",
        workspace_root="D:\\AI_COMMAND_CENTER",
        working_directory="D:\\AI_COMMAND_CENTER",
        permissions={
            "read",
            "write",
            "execute",
        },
        metadata={
            "priority": "high",
            "source": "manual-test",
            "execution_id": "execution-service-001",
        },
    )

    steps = [
        {
            "name": "analyze",
            "description": "Analyze application requirements.",
            "action": "analyze_requirements",
        },
        {
            "name": "generate_code",
            "description": "Generate application code.",
            "action": "generate_code",
        },
    ]

    # -------------------------------------------------
    # SUCCESS PATH
    # -------------------------------------------------

    response = service.execute(
        execution_request=request,
        steps=steps,
    )

    print("SUCCESS:", response.success)
    print("EXECUTION ID:", response.execution_id)
    print("PLAN ID:", response.plan_id)
    print("OUTPUT:", response.output)
    print("STATUS:", response.get_metadata(
        "execution_status"
    ))

    if not response.is_success():
        message = (
            response.error.message
            if response.error
            else "Execution failed."
        )

        raise RuntimeError(message)

    if response.execution_id != (
        "execution-service-001"
    ):
        raise RuntimeError(
            "Execution ID was not preserved."
        )

    if response.plan_id is None:
        raise RuntimeError(
            "Plan ID should be present."
        )

    if response.output is None:
        raise RuntimeError(
            "Execution output should be present."
        )

    if response.get_metadata(
        "execution_status"
    ) != "completed":
        raise RuntimeError(
            "Execution status should be completed."
        )

    if response.get_metadata(
        "workspace_root"
    ) != "D:\\AI_COMMAND_CENTER":
        raise RuntimeError(
            "Workspace metadata was not preserved."
        )

    print("REQUEST → ENGINE: PASS")
    print("ENGINE → RESPONSE: PASS")
    print("METADATA: PASS")
    print("SUCCESS PATH: PASS")

    # -------------------------------------------------
    # FAILURE PATH
    # -------------------------------------------------

    failure_request = ExecutionRequest.create(
        request="Test missing action.",
        user_id="user-001",
        task_id="failure-task",
        agent_id="agent-001",
        metadata={
            "execution_id": "execution-failure-001",
        },
    )

    failure = service.execute(
        execution_request=failure_request,
        steps=[
            {
                "name": "missing",
                "description": "Test missing action.",
                "action": "action_not_registered",
            }
        ],
    )

    print(
        "FAILURE:",
        failure.success,
    )

    print(
        "FAILURE CODE:",
        failure.error.code
        if failure.error
        else None,
    )

    print(
        "FAILURE MESSAGE:",
        failure.error.message
        if failure.error
        else None,
    )

    if failure.is_success():
        raise RuntimeError(
            "Missing action should fail."
        )

    if failure.execution_id != (
        "execution-failure-001"
    ):
        raise RuntimeError(
            "Failure execution ID was not preserved."
        )

    if failure.error is None:
        raise RuntimeError(
            "Failure response must contain an error."
        )

    if failure.error.code != (
        "ACTION_NOT_FOUND"
    ):
        raise RuntimeError(
            "Unexpected failure code."
        )

    print("FAILURE RESPONSE: PASS")
    print("ERROR PROPAGATION: PASS")

    # -------------------------------------------------
    # INVALID REQUEST
    # -------------------------------------------------

    invalid = service.execute(
        execution_request="invalid-request",
        steps=steps,
    )

    print(
        "INVALID REQUEST:",
        invalid.error.code
        if invalid.error
        else None,
    )

    if invalid.is_success():
        raise RuntimeError(
            "Invalid request should fail."
        )

    if invalid.error is None:
        raise RuntimeError(
            "Invalid request must contain an error."
        )

    if invalid.error.code != (
        "INVALID_EXECUTION_REQUEST"
    ):
        raise RuntimeError(
            "Unexpected invalid request error."
        )

    print("INVALID REQUEST: PASS")

    print()
    print("=" * 60)
    print("EXECUTION SERVICE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()