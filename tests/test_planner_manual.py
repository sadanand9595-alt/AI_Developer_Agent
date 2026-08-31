from dataclasses import replace

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

    # Non-string request protection
    invalid_result = planner.create_plan(123)

    if invalid_result.is_success():
        raise RuntimeError(
            "Non-string request should be rejected."
        )

    if invalid_result.error.code != "INVALID_REQUEST":
        raise RuntimeError(
            "Unexpected non-string request error: "
            f"{invalid_result.error.code}"
        )

    print("NON-STRING REQUEST PROTECTION: PASS")

    # Non-string plan/step fields must not crash validate_plan
    bad_plan_id = replace(plan, plan_id=123)

    bad_plan_id_result = planner.validate_plan(bad_plan_id)

    if bad_plan_id_result.is_success():
        raise RuntimeError(
            "Non-string plan ID should be rejected."
        )

    if bad_plan_id_result.error.code != "INVALID_PLAN_ID":
        raise RuntimeError(
            "Unexpected non-string plan ID error: "
            f"{bad_plan_id_result.error.code}"
        )

    bad_step = replace(step, step_id=123)
    bad_step_plan = replace(plan, steps=(bad_step,))

    bad_step_result = planner.validate_plan(bad_step_plan)

    if bad_step_result.is_success():
        raise RuntimeError(
            "Non-string step ID should be rejected."
        )

    if bad_step_result.error.code != "INVALID_STEP_ID":
        raise RuntimeError(
            "Unexpected non-string step ID error: "
            f"{bad_step_result.error.code}"
        )

    print("NON-STRING FIELD VALIDATION: PASS")

    print()
    print("=" * 60)
    print("PLANNER: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()