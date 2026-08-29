from core.execution_runtime_factory import (
    ExecutionRuntimeFactory,
)
from core.execution_runtime_service import (
    ExecutionRuntimeService,
)


def main() -> None:
    # -------------------------------------------------
    # CREATE SERVICE
    # -------------------------------------------------

    service = ExecutionRuntimeFactory.create()

    if not isinstance(
        service,
        ExecutionRuntimeService,
    ):
        raise RuntimeError(
            "Factory should return ExecutionRuntimeService."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # START EXECUTION
    # -------------------------------------------------

    record = service.start(
        execution_id="factory-execution-001",
        task_id="factory-task-001",
        total_steps=2,
        metadata={
            "source": "factory-test",
        },
    )

    if record.execution_id != (
        "factory-execution-001"
    ):
        raise RuntimeError(
            "Execution ID is incorrect."
        )

    if record.status != "running":
        raise RuntimeError(
            "Execution should be running."
        )

    print("START: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    service.start_step(
        execution_id="factory-execution-001",
        step_name="analyze",
        task_id="factory-task-001",
    )

    service.complete_step(
        execution_id="factory-execution-001",
        step_name="analyze",
        task_id="factory-task-001",
    )

    progress = service.get_progress(
        "factory-execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.completed_steps != 1:
        raise RuntimeError(
            "Expected one completed step."
        )

    if progress.progress_percent != 50.0:
        raise RuntimeError(
            "Progress should be 50%."
        )

    print("STEP 1: PASS")

    # -------------------------------------------------
    # STEP 2
    # -------------------------------------------------

    service.start_step(
        execution_id="factory-execution-001",
        step_name="generate",
        task_id="factory-task-001",
    )

    service.complete_step(
        execution_id="factory-execution-001",
        step_name="generate",
        task_id="factory-task-001",
    )

    progress = service.get_progress(
        "factory-execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.progress_percent != 100.0:
        raise RuntimeError(
            "Progress should be 100%."
        )

    if progress.status != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    print("STEP 2: PASS")
    print("COMPLETION: PASS")

    # -------------------------------------------------
    # OBSERVATION
    # -------------------------------------------------

    observation = service.get_observation(
        "factory-execution-001"
    )

    if observation is None:
        raise RuntimeError(
            "Observation should exist."
        )

    if observation.status != "completed":
        raise RuntimeError(
            "Observer should report completed."
        )

    if observation.progress_percent != 100.0:
        raise RuntimeError(
            "Observer progress should be 100%."
        )

    print("OBSERVATION: PASS")

    # -------------------------------------------------
    # AUDIT
    # -------------------------------------------------

    audit = service.get_audit(
        "factory-execution-001"
    )

    if not audit:
        raise RuntimeError(
            "Factory-created runtime should record audit events."
        )

    audit_types = {
        item.event_type
        for item in audit
    }

    required_events = {
        "execution.started",
        "execution.step_started",
        "execution.step_completed",
        "execution.completed",
    }

    missing = required_events - audit_types

    if missing:
        raise RuntimeError(
            f"Missing audit events: {sorted(missing)}"
        )

    print("AUDIT: PASS")

    # -------------------------------------------------
    # ACTIVE COUNT
    # -------------------------------------------------

    if service.active_count() != 0:
        raise RuntimeError(
            "Completed execution must not be active."
        )

    print("ACTIVE COUNT: PASS")

    # -------------------------------------------------
    # FACTORY ISOLATION
    # -------------------------------------------------

    second_service = (
        ExecutionRuntimeFactory.create()
    )

    if second_service.get(
        "factory-execution-001"
    ) is not None:
        raise RuntimeError(
            "Factory instances must have isolated state."
        )

    if second_service.audit_count() != 0:
        raise RuntimeError(
            "Second factory instance should have empty audit."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    service.close()
    second_service.close()

    print("CLOSE: PASS")

    print()
    print("=" * 60)
    print("EXECUTION RUNTIME FACTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()