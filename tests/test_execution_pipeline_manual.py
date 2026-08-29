from core.execution_pipeline import (
    ExecutionPipeline,
    PipelineStage,
)
from core.result import Result


def main() -> None:
    pipeline = ExecutionPipeline()

    pipeline.add_stage(
        PipelineStage(
            name="prepare",
            handler=lambda value: Result.ok(
                f"{value}-prepared"
            ),
        )
    )

    pipeline.add_stage(
        PipelineStage(
            name="execute",
            handler=lambda value: Result.ok(
                f"{value}-executed"
            ),
        )
    )

    pipeline.add_stage(
        PipelineStage(
            name="validate",
            handler=lambda value: Result.ok(
                f"{value}-validated"
            ),
        )
    )

    print(
        "STAGES:",
        pipeline.stage_names(),
    )

    print(
        "STAGE COUNT:",
        pipeline.stage_count(),
    )

    result = pipeline.execute("task")

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    print(
        "RESULT:",
        result.require_data(),
    )

    if result.require_data() != (
        "task-prepared-executed-validated"
    ):
        raise RuntimeError(
            "Unexpected pipeline result."
        )

    print("SUCCESS PIPELINE: PASS")

    # Failure propagation test.
    failure_pipeline = ExecutionPipeline()

    failure_pipeline.add_stage(
        PipelineStage(
            name="prepare",
            handler=lambda value: Result.ok(
                value
            ),
        )
    )

    failure_pipeline.add_stage(
        PipelineStage(
            name="failing_stage",
            handler=lambda value: Result.fail(
                "TEST_FAILURE",
                "Simulated pipeline failure.",
            ),
        )
    )

    failure_pipeline.add_stage(
        PipelineStage(
            name="should_not_run",
            handler=lambda value: Result.ok(
                "unexpected"
            ),
        )
    )

    failure = failure_pipeline.execute(
        "task"
    )

    if failure.is_success():
        raise RuntimeError(
            "Failure pipeline should fail."
        )

    print(
        "FAILURE CODE:",
        failure.error.code,
    )

    print(
        "FAILED STAGE:",
        failure.error.details.get(
            "failed_stage"
        ),
    )

    if failure.error.code != "TEST_FAILURE":
        raise RuntimeError(
            "Unexpected failure code."
        )

    if (
        failure.error.details.get(
            "failed_stage"
        )
        != "failing_stage"
    ):
        raise RuntimeError(
            "Failed stage was not reported correctly."
        )

    print("FAILURE PROPAGATION: PASS")

    # Duplicate stage protection.
    duplicate_pipeline = ExecutionPipeline()

    duplicate_pipeline.add_stage(
        PipelineStage(
            name="unique",
            handler=lambda value: Result.ok(value),
        )
    )

    try:
        duplicate_pipeline.add_stage(
            PipelineStage(
                name="unique",
                handler=lambda value: Result.ok(value),
            )
        )
    except ValueError:
        print("DUPLICATE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Duplicate stage should be rejected."
        )

    print()
    print("=" * 60)
    print("EXECUTION PIPELINE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()