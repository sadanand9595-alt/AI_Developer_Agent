from core.planner import Planner


def main() -> None:
    planner = Planner()

    # Create plan
    result = planner.create_plan(
        "Create a production-ready CRM application."
    )

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    plan = result.require_data()

    print("PLAN ID:", plan.plan_id)
    print("REQUEST:", plan.request)
    print("STEP COUNT:", plan.step_count)

    if not plan.plan_id:
        raise RuntimeError(
            "Plan ID was not generated."
        )

    if plan.request != (
        "Create a production-ready CRM application."
    ):
        raise RuntimeError(
            "Plan request was not stored correctly."
        )

    if plan.step_count != 1:
        raise RuntimeError(
            "Expected exactly one initial planning step."
        )

    step = plan.steps[0]

    print("STEP ID:", step.step_id)
    print("STEP NAME:", step.name)
    print("STEP ACTION:", step.action)
    print("STEP ORDER:", step.order)

    if step.order != 1:
        raise RuntimeError(
            "First step must have order 1."
        )

    print("PLAN CREATION: PASS")

    # Validate plan
    validation = planner.validate_plan(
        plan
    )

    if validation.is_failure():
        raise RuntimeError(
            validation.error.message
        )

    print("PLAN VALIDATION: PASS")

    # Empty request protection
    empty_result = planner.create_plan(
        "   "
    )

    if empty_result.is_success():
        raise RuntimeError(
            "Empty request should be rejected."
        )

    print(
        "EMPTY REQUEST:",
        empty_result.error.code,
    )

    if empty_result.error.code != "EMPTY_REQUEST":
        raise RuntimeError(
            "Unexpected empty request error."
        )

    print("EMPTY REQUEST PROTECTION: PASS")

    print()
    print("=" * 60)
    print("PLANNER: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()