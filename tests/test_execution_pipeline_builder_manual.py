from core.execution_pipeline_builder import (
    ExecutionPipelineBuilder,
)
from core.result import Result


def main() -> None:
    builder = ExecutionPipelineBuilder()

    builder.add_stage(
        "prepare",
        lambda value: Result.ok(
            f"{value}-prepared"
        ),
    )

    builder.add_stage(
        "execute",
        lambda value: Result.ok(
            f"{value}-executed"
        ),
    )

    builder.add_passthrough_stage(
        "validate"
    )

    print(
        "STAGES:",
        builder.stage_names(),
    )

    print(
        "STAGE COUNT:",
        builder.stage_count(),
    )

    if builder.stage_count() != 3:
        raise RuntimeError(
            "Expected exactly 3 pipeline stages."
        )

    pipeline = builder.build()

    result = pipeline.execute("task")

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    print(
        "RESULT:",
        result.require_data(),
    )

    expected = "task-prepared-executed"

    if result.require_data() != expected:
        raise RuntimeError(
            f"Unexpected result: {result.require_data()}"
        )

    print("BUILD: PASS")
    print("EXECUTION: PASS")

    # Reset test.
    builder.reset()

    if builder.stage_count() != 0:
        raise RuntimeError(
            "Builder reset should remove all stages."
        )

    print("RESET: PASS")

    # Invalid stage name test.
    try:
        builder.add_stage(
            "",
            lambda value: Result.ok(value),
        )
    except ValueError:
        print("INVALID NAME PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Empty stage name should be rejected."
        )

    # Invalid handler test.
    try:
        builder.add_stage(
            "invalid_handler",
            "not-callable",
        )
    except TypeError:
        print("INVALID HANDLER PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Non-callable handler should be rejected."
        )

    print()
    print("=" * 60)
    print("EXECUTION PIPELINE BUILDER: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()