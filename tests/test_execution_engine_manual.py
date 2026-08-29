from core.action_registry import ActionRegistry
from core.execution_engine import ExecutionEngine
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

    def implement(context: PipelineContext):
        return Result.ok(
            {
                "stage": "implement",
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
        implement,
    )

    engine = ExecutionEngine(
        registry
    )

    context = PipelineContext(
        task_id="task-001",
        user_id="user-001",
        agent_id="agent-001",
    )

    steps = [
        {
            "name": "analyze",
            "description": "Analyze requirements.",
            "action": "analyze_requirements",
        },
        {
            "name": "implement",
            "description": "Generate application code.",
            "action": "generate_code",
        },
    ]

    result = engine.execute(
        request="Create a production-ready application.",
        steps=steps,
        context=context,
    )

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    final_context = result.require_data()

    print(
        "EXECUTION ID:",
        final_context.execution_id,
    )

    print(
        "PLAN ID:",
        final_context.get_metadata("plan_id"),
    )

    print(
        "STEP COUNT:",
        final_context.get_metadata("step_count"),
    )

    print(
        "STATUS:",
        final_context.get_metadata(
            "execution_status"
        ),
    )

    print(
        "STAGE RESULTS:",
        final_context.stage_results,
    )

    if final_context.get_metadata(
        "execution_status"
    ) != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    if len(
        final_context.stage_results
    ) != 2:
        raise RuntimeError(
            "Expected two stage results."
        )

    print("ENGINE EXECUTION: PASS")
    print("COORDINATOR INTEGRATION: PASS")
    print("MULTI-STAGE EXECUTION: PASS")

    # -------------------------------------------------
    # INVALID CONTEXT
    # -------------------------------------------------

    invalid_context = engine.execute(
        request="Invalid context test.",
        steps=steps,
        context="invalid",
    )

    if invalid_context.is_success():
        raise RuntimeError(
            "Invalid context should be rejected."
        )

    print(
        "INVALID CONTEXT:",
        invalid_context.error.code,
    )

    if invalid_context.error.code != (
        "INVALID_PIPELINE_CONTEXT"
    ):
        raise RuntimeError(
            "Unexpected invalid context error."
        )

    print("CONTEXT VALIDATION: PASS")

    # -------------------------------------------------
    # MISSING ACTION
    # -------------------------------------------------

    failure_context = PipelineContext(
        task_id="failure-task",
        user_id="user-001",
        agent_id="agent-001",
    )

    failure = engine.execute(
        request="Missing action test.",
        steps=[
            {
                "name": "missing",
                "description": "Test missing action.",
                "action": "action_not_registered",
            }
        ],
        context=failure_context,
    )

    if failure.is_success():
        raise RuntimeError(
            "Missing action should fail."
        )

    print(
        "MISSING ACTION:",
        failure.error.code,
    )

    if failure.error.code != "ACTION_NOT_FOUND":
        raise RuntimeError(
            "Unexpected missing action error."
        )

    print("FAILURE PROPAGATION: PASS")

    print()
    print("=" * 60)
    print("EXECUTION ENGINE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()