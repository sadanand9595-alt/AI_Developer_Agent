from core.plan_builder import PlanBuilder


def main() -> None:
    builder = PlanBuilder(
        "Create a production-ready CRM application."
    )

    builder.add_step(
        name="analyze",
        description="Analyze the CRM requirements.",
        action="analyze_requirements",
    )

    builder.add_step(
        name="design",
        description="Create the application architecture.",
        action="design_architecture",
        requires_approval=True,
    )

    builder.add_step(
        name="implement",
        description="Implement the application code.",
        action="generate_code",
        metadata={
            "language": "python",
        },
    )

    print(
        "STEP COUNT:",
        builder.step_count(),
    )

    if builder.step_count() != 3:
        raise RuntimeError(
            "Expected 3 plan steps."
        )

    result = builder.build()

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    plan = result.require_data()

    print(
        "PLAN ID:",
        plan.plan_id,
    )

    print(
        "REQUEST:",
        plan.request,
    )

    print(
        "PLAN STEPS:",
        plan.step_count,
    )

    for step in plan.steps:
        print(
            f"STEP {step.order}: "
            f"{step.name} → {step.action}"
        )

    if plan.steps[0].order != 1:
        raise RuntimeError(
            "First step must have order 1."
        )

    if plan.steps[1].order != 2:
        raise RuntimeError(
            "Second step must have order 2."
        )

    if plan.steps[2].order != 3:
        raise RuntimeError(
            "Third step must have order 3."
        )

    if not plan.steps[1].requires_approval:
        raise RuntimeError(
            "Design step should require approval."
        )

    if (
        plan.steps[2].metadata.get("language")
        != "python"
    ):
        raise RuntimeError(
            "Step metadata was not stored correctly."
        )

    print("MULTI-STEP PLAN: PASS")
    print("ORDERING: PASS")
    print("APPROVAL FLAG: PASS")
    print("METADATA: PASS")

    # Empty builder test.
    empty_builder = PlanBuilder(
        "Empty plan test"
    )

    empty_result = empty_builder.build()

    if empty_result.is_success():
        raise RuntimeError(
            "Empty plan should not be buildable."
        )

    print(
        "EMPTY PLAN:",
        empty_result.error.code,
    )

    if empty_result.error.code != "EMPTY_PLAN":
        raise RuntimeError(
            "Unexpected empty plan error."
        )

    print("EMPTY PLAN PROTECTION: PASS")

    # Clear test.
    builder.clear()

    if builder.step_count() != 0:
        raise RuntimeError(
            "Builder should contain zero steps after clear."
        )

    print("CLEAR: PASS")

    # -------------------------------------------------
    # INVALID REQUEST TYPE
    # -------------------------------------------------

    for invalid_request in (None, 123, ["not", "a", "string"]):
        try:
            PlanBuilder(invalid_request)
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Non-string request should be rejected."
            )

    print("INVALID REQUEST TYPE: PASS")

    # -------------------------------------------------
    # INVALID STEP FIELD TYPES
    # -------------------------------------------------

    type_check_builder = PlanBuilder(
        "Invalid step field type test."
    )

    invalid_step_calls = [
        {
            "name": None,
            "description": "d",
            "action": "a",
        },
        {
            "name": "n",
            "description": None,
            "action": "a",
        },
        {
            "name": "n",
            "description": "d",
            "action": None,
        },
        {
            "name": "n",
            "description": "d",
            "action": "a",
            "requires_approval": "yes",
        },
        {
            "name": "n",
            "description": "d",
            "action": "a",
            "metadata": 123,
        },
        {
            "name": "n",
            "description": "d",
            "action": "a",
            "metadata": "bad",
        },
    ]

    for kwargs in invalid_step_calls:
        try:
            type_check_builder.add_step(**kwargs)
        except ValueError:
            pass
        else:
            raise RuntimeError(
                f"Invalid step field should be rejected: {kwargs}"
            )

    if type_check_builder.step_count() != 0:
        raise RuntimeError(
            "Rejected steps must not be added."
        )

    print("INVALID STEP FIELD TYPES: PASS")

    print()
    print("=" * 60)
    print("PLAN BUILDER: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()