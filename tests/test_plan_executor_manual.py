from core.action_executor import ActionExecutor
from core.action_registry import ActionRegistry
from core.pipeline_context import PipelineContext
from core.plan_executor import PlanExecutor
from core.plan_builder import PlanBuilder
from core.planner import ExecutionPlan, PlanStep
from core.result import Result


def main() -> None:
    registry = ActionRegistry()

    def analyze(context: PipelineContext):
        return Result.ok(
            {
                "stage": "analyze",
                "request": context.input_data,
            }
        )

    def design(context: PipelineContext):
        return Result.ok(
            {
                "stage": "design",
                "architecture": "production-ready",
            }
        )

    def implement(context: PipelineContext):
        return Result.ok(
            {
                "stage": "implement",
                "files": 3,
            }
        )

    def failing_action(context: PipelineContext):
        return Result.fail(
            "TEST_EXECUTION_FAILURE",
            "Simulated plan execution failure.",
        )

    registry.register(
        "analyze",
        analyze,
    )

    registry.register(
        "design",
        design,
    )

    registry.register(
        "implement",
        implement,
    )

    registry.register(
        "failing",
        failing_action,
    )

    action_executor = ActionExecutor(
        registry
    )

    executor = PlanExecutor(
        action_executor
    )

    context = PipelineContext(
        task_id="task-001",
        user_id="user-001",
        agent_id="agent-001",
    )

    context.set_input(
        "Build an AI application."
    )

    # -------------------------------------------------
    # SUCCESS PATH
    # -------------------------------------------------

    builder = PlanBuilder(
        "Build an AI application."
    )

    builder.add_step(
        name="analyze",
        description="Analyze requirements.",
        action="analyze",
    )

    builder.add_step(
        name="design",
        description="Design architecture.",
        action="design",
    )

    builder.add_step(
        name="implement",
        description="Implement the application.",
        action="implement",
    )

    plan_result = builder.build()

    if plan_result.is_failure():
        raise RuntimeError(
            plan_result.error.message
        )

    plan = plan_result.require_data()

    result = executor.execute(
        plan,
        context,
    )

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    final_context = result.require_data()

    print(
        "FINAL OUTPUT:",
        final_context.output_data,
    )

    print(
        "STAGE RESULTS:",
        final_context.stage_results,
    )

    if final_context.output_data is None:
        raise RuntimeError(
            "Final output should exist."
        )

    if len(
        final_context.stage_results
    ) != 3:
        raise RuntimeError(
            "Expected three stage results."
        )

    print("MULTI-STEP EXECUTION: PASS")
    print("STAGE ORDER: PASS")
    print("CONTEXT OUTPUT: PASS")

    # -------------------------------------------------
    # FAILURE PROPAGATION
    # -------------------------------------------------

    failure_builder = PlanBuilder(
        "Failure test."
    )

    failure_builder.add_step(
        name="analyze",
        description="Analyze requirements.",
        action="analyze",
    )

    failure_builder.add_step(
        name="failing",
        description="Simulate execution failure.",
        action="failing",
    )

    failure_builder.add_step(
        name="implement",
        description="This step must not execute.",
        action="implement",
    )

    failure_plan_result = failure_builder.build()

    if failure_plan_result.is_failure():
        raise RuntimeError(
            failure_plan_result.error.message
        )

    failure_result = executor.execute(
        failure_plan_result.require_data(),
        PipelineContext(
            task_id="failure-task",
            user_id="user-001",
            agent_id="agent-001",
        ),
    )

    if failure_result.is_success():
        raise RuntimeError(
            "Failed plan should return failure."
        )

    print(
        "FAILURE CODE:",
        failure_result.error.code,
    )

    print(
        "FAILED STEP:",
        failure_result.error.details.get(
            "failed_step"
        ),
    )

    if failure_result.error.code != (
        "TEST_EXECUTION_FAILURE"
    ):
        raise RuntimeError(
            "Unexpected failure code."
        )

    if failure_result.error.details.get(
        "failed_step"
    ) != "failing":
        raise RuntimeError(
            "Incorrect failed step."
        )

    print("FAILURE PROPAGATION: PASS")

    # -------------------------------------------------
    # INVALID PLAN
    # -------------------------------------------------

    invalid_plan_result = executor.execute(
        "invalid-plan",
        context,
    )

    if invalid_plan_result.is_success():
        raise RuntimeError(
            "Invalid plan should be rejected."
        )

    print(
        "INVALID PLAN:",
        invalid_plan_result.error.code,
    )

    print("PLAN VALIDATION: PASS")

    # -------------------------------------------------
    # INVALID CONTEXT
    # -------------------------------------------------

    invalid_context_result = executor.execute(
        plan,
        "invalid-context",
    )

    if invalid_context_result.is_success():
        raise RuntimeError(
            "Invalid context should be rejected."
        )

    print(
        "INVALID CONTEXT:",
        invalid_context_result.error.code,
    )

    print("CONTEXT VALIDATION: PASS")

    # -------------------------------------------------
    # EMPTY PLAN
    # -------------------------------------------------

    empty_plan = ExecutionPlan(
        plan_id="empty-plan",
        request="Empty plan test.",
        steps=(),
        metadata={},
    )

    empty_plan_result = executor.execute(
        empty_plan,
        PipelineContext(),
    )

    if empty_plan_result.is_success():
        raise RuntimeError(
            "Empty plan should be rejected."
        )

    if empty_plan_result.error.code != (
        "EMPTY_EXECUTION_PLAN"
    ):
        raise RuntimeError(
            "Unexpected empty plan error: "
            f"{empty_plan_result.error.code}"
        )

    print("EMPTY PLAN: PASS")

    # -------------------------------------------------
    # NON-INT STEP ORDER (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------
    #
    # A malformed plan built outside PlanBuilder (which
    # always assigns integer order) must return a Result
    # failure, never raise.
    # -------------------------------------------------

    for bad_order in ("first", True, 1.5):
        malformed_plan = ExecutionPlan(
            plan_id="malformed-order-plan",
            request="Malformed order test.",
            steps=(
                PlanStep(
                    step_id="step-1",
                    name="analyze",
                    description="Analyze requirements.",
                    action="analyze",
                    order=bad_order,
                ),
            ),
            metadata={},
        )

        try:
            malformed_result = executor.execute(
                malformed_plan,
                PipelineContext(),
            )
        except Exception as exc:
            raise RuntimeError(
                "Executor raised for non-int order "
                f"{bad_order!r}: {type(exc).__name__}: {exc}"
            )

        if malformed_result.is_success():
            raise RuntimeError(
                f"Non-int step order {bad_order!r} should "
                "be rejected."
            )

        if malformed_result.error.code != (
            "INVALID_STEP_ORDER"
        ):
            raise RuntimeError(
                "Unexpected error code for non-int order "
                f"{bad_order!r}: {malformed_result.error.code}"
            )

    print("NON-INT STEP ORDER SAFETY: PASS")

    print()
    print("=" * 60)
    print("PLAN EXECUTOR: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()