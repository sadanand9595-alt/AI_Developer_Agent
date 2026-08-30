from core.action_executor import ActionExecutor
from core.action_registry import ActionRegistry
from core.pipeline_context import PipelineContext
from core.plan_builder import PlanBuilder
from core.planner import PlanStep
from core.result import Result


def main() -> None:
    registry = ActionRegistry()

    def analyze_handler(context: PipelineContext):
        return Result.ok(
            {
                "status": "analyzed",
                "request": context.input_data,
            }
        )

    def failing_handler(context: PipelineContext):
        return Result.fail(
            "TEST_ACTION_FAILURE",
            "Simulated action failure.",
        )

    registry.register(
        "analyze_requirements",
        analyze_handler,
    )

    registry.register(
        "failing_action",
        failing_handler,
    )

    executor = ActionExecutor(
        registry
    )

    context = PipelineContext(
        task_id="task-001",
        user_id="user-001",
        agent_id="agent-001",
    )

    context.set_input(
        "Create a CRM application."
    )

    # -------------------------------------------------
    # SUCCESS PATH
    # -------------------------------------------------

    builder = PlanBuilder(
        "Create a CRM application."
    )

    builder.add_step(
        name="analyze",
        description="Analyze the CRM request.",
        action="analyze_requirements",
    )

    plan_result = builder.build()

    if plan_result.is_failure():
        raise RuntimeError(
            plan_result.error.message
        )

    plan = plan_result.require_data()

    step = plan.steps[0]

    result = executor.execute_step(
        step,
        context,
    )

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    print(
        "SUCCESS RESULT:",
        result.require_data(),
    )

    if result.require_data()["status"] != "analyzed":
        raise RuntimeError(
            "Unexpected action result."
        )

    print("SUCCESS EXECUTION: PASS")

    # Stage result must be stored.
    stage_result = context.get_stage_result(
        "analyze"
    )

    print(
        "STAGE RESULT:",
        stage_result,
    )

    if stage_result is None:
        raise RuntimeError(
            "Stage result was not stored."
        )

    print("CONTEXT UPDATE: PASS")

    # -------------------------------------------------
    # MISSING ACTION
    # -------------------------------------------------

    missing_builder = PlanBuilder(
        "Missing action test."
    )

    missing_builder.add_step(
        name="missing",
        description="Test missing action.",
        action="does_not_exist",
    )

    missing_plan = missing_builder.build()

    if missing_plan.is_failure():
        raise RuntimeError(
            missing_plan.error.message
        )

    missing_result = executor.execute_step(
        missing_plan.require_data().steps[0],
        context,
    )

    if missing_result.is_success():
        raise RuntimeError(
            "Missing action should fail."
        )

    print(
        "MISSING ACTION:",
        missing_result.error.code,
    )

    if missing_result.error.code != (
        "ACTION_NOT_FOUND"
    ):
        raise RuntimeError(
            "Unexpected missing action error."
        )

    print("MISSING ACTION: PASS")

    # -------------------------------------------------
    # ACTION FAILURE
    # -------------------------------------------------

    failure_builder = PlanBuilder(
        "Failure test."
    )

    failure_builder.add_step(
        name="failure",
        description="Test action failure.",
        action="failing_action",
    )

    failure_plan = failure_builder.build()

    if failure_plan.is_failure():
        raise RuntimeError(
            failure_plan.error.message
        )

    failure_result = executor.execute_step(
        failure_plan.require_data().steps[0],
        context,
    )

    if failure_result.is_success():
        raise RuntimeError(
            "Failing action should return failure."
        )

    print(
        "ACTION FAILURE:",
        failure_result.error.code,
    )

    if failure_result.error.code != (
        "TEST_ACTION_FAILURE"
    ):
        raise RuntimeError(
            "Unexpected action failure code."
        )

    print("FAILURE PROPAGATION: PASS")

    # -------------------------------------------------
    # INVALID CONTEXT
    # -------------------------------------------------

    invalid_context_result = executor.execute_step(
        step,
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
    # NON-STRING ACTION (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------
    #
    # PlanStep is a plain dataclass with no field
    # validation, so ActionExecutor may be called
    # directly with a step whose action was never
    # normalized by PlanBuilder/PlanValidator. This
    # must return a Result failure, never raise.
    # -------------------------------------------------

    for bad_action in (None, 123, ["not", "a", "string"]):
        malformed_step = PlanStep(
            step_id="malformed-step",
            name="malformed",
            description="Non-string action test.",
            action=bad_action,
            order=1,
        )

        try:
            malformed_result = executor.execute_step(
                malformed_step,
                context,
            )
        except Exception as exc:
            raise RuntimeError(
                "Executor raised for non-string action "
                f"{bad_action!r}: {type(exc).__name__}: {exc}"
            )

        if malformed_result.is_success():
            raise RuntimeError(
                f"Non-string action {bad_action!r} should "
                "be rejected."
            )

        if malformed_result.error.code != "INVALID_ACTION":
            raise RuntimeError(
                "Unexpected error code for non-string "
                f"action {bad_action!r}: "
                f"{malformed_result.error.code}"
            )

    print("NON-STRING ACTION SAFETY: PASS")

    print()
    print("=" * 60)
    print("ACTION EXECUTOR: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()