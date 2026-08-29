from core.pipeline_context import PipelineContext


def main() -> None:
    context = PipelineContext(
        task_id="task-001",
        user_id="user-001",
        agent_id="agent-001",
    )

    print("EXECUTION ID:", context.execution_id)

    if not context.execution_id:
        raise RuntimeError(
            "Execution ID should be generated."
        )

    print("IDENTITY: PASS")

    # Input
    context.set_input(
        {
            "request": "Create a Python application.",
        }
    )

    print(
        "INPUT:",
        context.input_data,
    )

    if context.input_data is None:
        raise RuntimeError(
            "Pipeline input was not stored."
        )

    print("INPUT: PASS")

    # Metadata
    context.set_metadata(
        "environment",
        "test",
    )

    context.set_metadata(
        "priority",
        "high",
    )

    print(
        "ENVIRONMENT:",
        context.get_metadata("environment"),
    )

    print(
        "PRIORITY:",
        context.get_metadata("priority"),
    )

    if not context.has_metadata(
        "environment"
    ):
        raise RuntimeError(
            "Metadata was not stored."
        )

    print("METADATA: PASS")

    # Stage results
    context.add_stage_result(
        "planner",
        {
            "steps": 3,
        },
    )

    context.add_stage_result(
        "executor",
        {
            "success": True,
        },
    )

    print(
        "PLANNER RESULT:",
        context.get_stage_result("planner"),
    )

    print(
        "EXECUTOR RESULT:",
        context.get_stage_result("executor"),
    )

    if context.get_stage_result(
        "planner"
    ) is None:
        raise RuntimeError(
            "Planner result was not stored."
        )

    print("STAGE RESULTS: PASS")

    # Output
    context.set_output(
        {
            "status": "completed",
        }
    )

    print(
        "OUTPUT:",
        context.output_data,
    )

    if context.output_data is None:
        raise RuntimeError(
            "Pipeline output was not stored."
        )

    print("OUTPUT: PASS")

    # Clear stage results
    context.clear_stage_results()

    if context.stage_results:
        raise RuntimeError(
            "Stage results should be empty after clear."
        )

    print("CLEAR STAGE RESULTS: PASS")

    # Validation
    try:
        context.set_metadata(
            "",
            "invalid",
        )
    except ValueError:
        print("INVALID METADATA KEY: PASS")
    else:
        raise RuntimeError(
            "Empty metadata key should be rejected."
        )

    try:
        context.add_stage_result(
            "",
            "invalid",
        )
    except ValueError:
        print("INVALID STAGE NAME: PASS")
    else:
        raise RuntimeError(
            "Empty stage name should be rejected."
        )

    print()
    print("=" * 60)
    print("PIPELINE CONTEXT: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()