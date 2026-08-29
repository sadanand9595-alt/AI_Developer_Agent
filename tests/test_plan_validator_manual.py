from dataclasses import replace

from core.plan_validator import PlanValidator
from core.planner import Planner


def main() -> None:
    planner = Planner()
    validator = PlanValidator()

    # -------------------------------------------------
    # VALID PLAN
    # -------------------------------------------------

    result = planner.create_plan(
        "Create a production-ready CRM application."
    )

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    plan = result.require_data()

    validation = validator.validate(plan)

    if validation.is_failure():
        raise RuntimeError(
            validation.error.message
        )

    print("VALID PLAN: PASS")

    # -------------------------------------------------
    # INVALID PLAN TYPE
    # -------------------------------------------------

    invalid_type = validator.validate(
        "not-a-plan"
    )

    if invalid_type.is_success():
        raise RuntimeError(
            "Invalid plan type should be rejected."
        )

    print(
        "INVALID PLAN TYPE:",
        invalid_type.error.code,
    )

    # -------------------------------------------------
    # EMPTY PLAN ID
    # -------------------------------------------------

    invalid_id = replace(
        plan,
        plan_id="",
    )

    invalid_id_result = validator.validate(
        invalid_id
    )

    if invalid_id_result.is_success():
        raise RuntimeError(
            "Empty plan ID should be rejected."
        )

    print(
        "INVALID PLAN ID:",
        invalid_id_result.error.code,
    )

    # -------------------------------------------------
    # INVALID STEP DESCRIPTION
    # -------------------------------------------------

    invalid_description_step = replace(
        plan.steps[0],
        description="",
    )

    invalid_description_plan = replace(
        plan,
        steps=(
            invalid_description_step,
        ),
    )

    invalid_description_result = validator.validate(
        invalid_description_plan
    )

    if invalid_description_result.is_success():
        raise RuntimeError(
            "Empty step description should be rejected."
        )

    print(
        "INVALID DESCRIPTION:",
        invalid_description_result.error.code,
    )

    # -------------------------------------------------
    # INVALID STEP ORDER
    # -------------------------------------------------

    invalid_order_step = replace(
        plan.steps[0],
        order=0,
    )

    invalid_order_plan = replace(
        plan,
        steps=(
            invalid_order_step,
        ),
    )

    invalid_order_result = validator.validate(
        invalid_order_plan
    )

    if invalid_order_result.is_success():
        raise RuntimeError(
            "Invalid step order should be rejected."
        )

    print(
        "INVALID ORDER:",
        invalid_order_result.error.code,
    )

    # -------------------------------------------------
    # DUPLICATE STEP ID
    # -------------------------------------------------

    first_step = plan.steps[0]

    duplicate_step = replace(
        first_step,
        order=2,
    )

    duplicate_id_plan = replace(
        plan,
        steps=(
            first_step,
            duplicate_step,
        ),
    )

    duplicate_id_result = validator.validate(
        duplicate_id_plan
    )

    if duplicate_id_result.is_success():
        raise RuntimeError(
            "Duplicate step ID should be rejected."
        )

    print(
        "DUPLICATE STEP ID:",
        duplicate_id_result.error.code,
    )

    # -------------------------------------------------
    # NON-SEQUENTIAL ORDER
    # -------------------------------------------------

    second_step = replace(
        first_step,
        step_id="second-step",
        name="second_step",
        description="Second execution step.",
        action="execute",
        order=3,
    )

    non_sequential_plan = replace(
        plan,
        steps=(
            first_step,
            second_step,
        ),
    )

    non_sequential_result = validator.validate(
        non_sequential_plan
    )

    if non_sequential_result.is_success():
        raise RuntimeError(
            "Non-sequential step order should be rejected."
        )

    print(
        "NON-SEQUENTIAL ORDER:",
        non_sequential_result.error.code,
    )

    print()
    print("=" * 60)
    print("PLAN VALIDATOR: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()