from core.execution_runtime import ExecutionRuntime
from core.execution_runtime_service import ExecutionRuntimeService


def main() -> None:
    runtime = ExecutionRuntime()

    service = ExecutionRuntimeService(
        runtime
    )

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    record = service.start(
        execution_id="execution-service-001",
        task_id="task-service-001",
        total_steps=2,
        metadata={
            "source": "manual-test",
        },
    )

    print(
        "STARTED:",
        record.execution_id,
    )

    print(
        "STATUS:",
        record.status,
    )

    if record.execution_id != (
        "execution-service-001"
    ):
        raise RuntimeError(
            "Execution ID was not preserved."
        )

    if record.status != "running":
        raise RuntimeError(
            "Execution should start as running."
        )

    if service.active_count() != 1:
        raise RuntimeError(
            "Expected one active execution."
        )

    print("START: PASS")
    print("ACTIVE COUNT: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    service.start_step(
        execution_id="execution-service-001",
        step_name="analyze",
        task_id="task-service-001",
    )

    progress = service.get_progress(
        "execution-service-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.current_step != "analyze":
        raise RuntimeError(
            "Current step should be analyze."
        )

    service.complete_step(
        execution_id="execution-service-001",
        step_name="analyze",
        task_id="task-service-001",
    )

    progress = service.get_progress(
        "execution-service-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.completed_steps != 1:
        raise RuntimeError(
            "One step should be completed."
        )

    if progress.progress_percent != 50.0:
        raise RuntimeError(
            "Progress should be 50%."
        )

    print(
        "STEP 1 PROGRESS:",
        progress.progress_percent,
    )

    print("STEP 1: PASS")

    # -------------------------------------------------
    # STEP 2
    # -------------------------------------------------

    service.start_step(
        execution_id="execution-service-001",
        step_name="generate",
        task_id="task-service-001",
    )

    service.complete_step(
        execution_id="execution-service-001",
        step_name="generate",
        task_id="task-service-001",
    )

    progress = service.get_progress(
        "execution-service-001"
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

    print(
        "FINAL PROGRESS:",
        progress.progress_percent,
    )

    print(
        "FINAL STATUS:",
        progress.status,
    )

    print("STEP 2: PASS")

    # -------------------------------------------------
    # EXECUTION STATE
    # -------------------------------------------------

    completed = service.get(
        "execution-service-001"
    )

    if completed is None:
        raise RuntimeError(
            "Execution record should exist."
        )

    if completed.status != "completed":
        raise RuntimeError(
            "Execution manager should report completed."
        )

    print("EXECUTION STATE: PASS")

    # -------------------------------------------------
    # OBSERVATION
    # -------------------------------------------------

    observation = service.get_observation(
        "execution-service-001"
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
        "execution-service-001"
    )

    if len(audit) == 0:
        raise RuntimeError(
            "Audit records should exist."
        )

    audit_types = [
        item.event_type
        for item in audit
    ]

    print(
        "AUDIT EVENTS:",
        audit_types,
    )

    if "execution.started" not in audit_types:
        raise RuntimeError(
            "Started event should be audited."
        )

    if (
        "execution.step_started"
        not in audit_types
    ):
        raise RuntimeError(
            "Step started event should be audited."
        )

    if (
        "execution.step_completed"
        not in audit_types
    ):
        raise RuntimeError(
            "Step completed event should be audited."
        )

    if (
        "execution.completed"
        not in audit_types
    ):
        raise RuntimeError(
            "Completed event should be audited."
        )

    print("AUDIT: PASS")

    # -------------------------------------------------
    # FAILURE
    # -------------------------------------------------

    service.start(
        execution_id="execution-service-002",
        task_id="task-service-002",
        total_steps=1,
    )

    service.start_step(
        execution_id="execution-service-002",
        step_name="generate_code",
        task_id="task-service-002",
    )

    failed = service.fail(
        execution_id="execution-service-002",
        error_code="GENERATION_FAILED",
        error_message="Generation test failed.",
        step_name="generate_code",
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    failure_audit = service.get_audit(
        "execution-service-002"
    )

    if not any(
        item.event_type
        == "execution.failed"
        for item in failure_audit
    ):
        raise RuntimeError(
            "Failure event should be audited."
        )

    print("FAILURE: PASS")

    # -------------------------------------------------
    # CANCEL
    # -------------------------------------------------

    service.start(
        execution_id="execution-service-003",
        task_id="task-service-003",
        total_steps=1,
    )

    cancelled = service.cancel(
        execution_id="execution-service-003"
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    cancel_audit = service.get_audit(
        "execution-service-003"
    )

    if not any(
        item.event_type
        == "execution.cancelled"
        for item in cancel_audit
    ):
        raise RuntimeError(
            "Cancellation event should be audited."
        )

    print("CANCEL: PASS")

    # -------------------------------------------------
    # INVALID RUNTIME
    # -------------------------------------------------

    try:
        ExecutionRuntimeService(
            "invalid-runtime"
        )
    except TypeError:
        print("INVALID RUNTIME: PASS")
    else:
        raise RuntimeError(
            "Invalid runtime should be rejected."
        )

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    service.close()

    print("CLOSE: PASS")

    print()
    print("=" * 60)
    print("EXECUTION RUNTIME SERVICE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()