from core.planning_pipeline import PlanningPipeline


def main() -> None:
    pipeline = PlanningPipeline()

    steps = [
        {
            "name": "analyze",
            "description": "Analyze the user requirements.",
            "action": "analyze_requirements",
        },
        {
            "name": "design",
            "description": "Design the application architecture.",
            "action": "design_architecture",
            "requires_approval": True,
        },
        {
            "name": "implement",
            "description": "Implement the required application code.",
            "action": "generate_code",
            "metadata": {
                "language": "python",
            },
        },
    ]

    result = pipeline.create_plan(
        request="Create a production-ready CRM application.",
        steps=steps,
    )

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    plan = result.require_data()

    print("PLAN ID:", plan.plan_id)
    print("REQUEST:", plan.request)
    print("STEP COUNT:", plan.step_count)

    if plan.step_count != 3:
        raise RuntimeError(
            "Expected 3 planning steps."
        )

    for step in plan.steps:
        print(
            f"STEP {step.order}: "
            f"{step.name} → {step.action}"
        )

    if plan.steps[0].order != 1:
        raise RuntimeError(
            "Step 1 order is invalid."
        )

    if plan.steps[1].order != 2:
        raise RuntimeError(
            "Step 2 order is invalid."
        )

    if plan.steps[2].order != 3:
        raise RuntimeError(
            "Step 3 order is invalid."
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
            "Step metadata was not preserved."
        )

    print("PLAN BUILD: PASS")
    print("PLAN VALIDATION: PASS")
    print("MULTI-STEP PIPELINE: PASS")

    # Empty request protection.
    empty_request = pipeline.create_plan(
        request="   ",
        steps=steps,
    )

    if empty_request.is_success():
        raise RuntimeError(
            "Empty request should be rejected."
        )

    print(
        "EMPTY REQUEST:",
        empty_request.error.code,
    )

    # Empty steps protection.
    empty_steps = pipeline.create_plan(
        request="Create an application.",
        steps=[],
    )

    if empty_steps.is_success():
        raise RuntimeError(
            "Empty steps should be rejected."
        )

    print(
        "EMPTY STEPS:",
        empty_steps.error.code,
    )

    # Invalid step protection.
    invalid_steps = pipeline.create_plan(
        request="Create an application.",
        steps=[
            {
                "name": "invalid",
                "description": "Invalid approval flag.",
                "action": "test",
                "requires_approval": "yes",
            }
        ],
    )

    if invalid_steps.is_success():
        raise RuntimeError(
            "Invalid approval flag should be rejected."
        )

    print(
        "INVALID STEP:",
        invalid_steps.error.code,
    )

    # Non-string request protection.
    #
    # A non-string request must return a Result failure,
    # not raise at the public boundary.

    for invalid_request in (None, 123, ["not", "a", "string"]):
        invalid_request_result = pipeline.create_plan(
            request=invalid_request,
            steps=steps,
        )

        if invalid_request_result.is_success():
            raise RuntimeError(
                "Non-string request should be rejected."
            )

        if invalid_request_result.error.code != (
            "INVALID_REQUEST"
        ):
            raise RuntimeError(
                "Unexpected invalid request error: "
                f"{invalid_request_result.error.code}"
            )

    print("INVALID REQUEST TYPE: PASS")

    print()
    print("=" * 60)
    print("PLANNING PIPELINE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()