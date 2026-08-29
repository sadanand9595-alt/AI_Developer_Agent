from core.execution_runtime import ExecutionRuntime


def main() -> None:
    runtime = ExecutionRuntime()

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    record = runtime.start(
        "execution-001",
        task_id="task-001",
        total_steps=3,
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

    if record.execution_id != "execution-001":
        raise RuntimeError(
            "Execution ID was not stored correctly."
        )

    if record.status != "running":
        raise RuntimeError(
            "Execution should start as running."
        )

    if runtime.active_count() != 1:
        raise RuntimeError(
            "Expected one active execution."
        )

    print("START: PASS")
    print("ACTIVE COUNT: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    runtime.start_step(
        "execution-001",
        "analyze",
        task_id="task-001",
    )

    progress = runtime.get_progress(
        "execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.current_step != "analyze":
        raise RuntimeError(
            "Current step should be analyze."
        )

    runtime.complete_step(
        "execution-001",
        "analyze",
        task_id="task-001",
    )

    progress = runtime.get_progress(
        "execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.completed_steps != 1:
        raise RuntimeError(
            "Expected one completed step."
        )

    if progress.progress_percent != (
        33.33
    ):
        raise RuntimeError(
            "Progress should be 33.33%."
        )

    print(
        "STEP 1 PROGRESS:",
        progress.progress_percent,
    )

    print("STEP 1: PASS")

    # -------------------------------------------------
    # STEP 2
    # -------------------------------------------------

    runtime.start_step(
        "execution-001",
        "generate",
        task_id="task-001",
    )

    runtime.complete_step(
        "execution-001",
        "generate",
        task_id="task-001",
    )

    progress = runtime.get_progress(
        "execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.completed_steps != 2:
        raise RuntimeError(
            "Expected two completed steps."
        )

    if progress.progress_percent != (
        66.67
    ):
        raise RuntimeError(
            "Progress should be 66.67%."
        )

    print(
        "STEP 2 PROGRESS:",
        progress.progress_percent,
    )

    print("STEP 2: PASS")

    # -------------------------------------------------
    # STEP 3
    # -------------------------------------------------

    runtime.start_step(
        "execution-001",
        "test",
        task_id="task-001",
    )

    runtime.complete_step(
        "execution-001",
        "test",
        task_id="task-001",
    )

    progress = runtime.get_progress(
        "execution-001"
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

    print("STEP 3: PASS")

    # -------------------------------------------------
    # COMPLETE EXECUTION RECORD
    # -------------------------------------------------

    # The final step already moved the tracker to
    # completed, but the manager record is completed
    # by the runtime integration.

    completed_record = runtime.get(
        "execution-001"
    )

    if completed_record is None:
        raise RuntimeError(
            "Execution record should exist."
        )

    if completed_record.status != (
        "completed"
    ):
        raise RuntimeError(
            "Manager record should be completed."
        )

    if runtime.active_count() != 0:
        raise RuntimeError(
            "Completed execution must not be active."
        )

    print("MANAGER COMPLETION: PASS")

    # -------------------------------------------------
    # OBSERVER
    # -------------------------------------------------

    observation = runtime.get_observation(
        "execution-001"
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

    print(
        "OBSERVED STATUS:",
        observation.status,
    )

    print(
        "OBSERVED PROGRESS:",
        observation.progress_percent,
    )

    print("OBSERVER: PASS")

    # -------------------------------------------------
    # AUDIT
    # -------------------------------------------------

    audit_records = runtime.get_audit(
        "execution-001"
    )

    if len(audit_records) < 1:
        raise RuntimeError(
            "Execution should have audit records."
        )

    audit_types = [
        record.event_type
        for record in audit_records
    ]

    print(
        "AUDIT EVENTS:",
        audit_types,
    )

    if (
        "execution.started"
        not in audit_types
    ):
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
    # FAILURE EXECUTION
    # -------------------------------------------------

    runtime.start(
        "execution-002",
        task_id="task-002",
        total_steps=2,
    )

    runtime.start_step(
        "execution-002",
        "generate_code",
        task_id="task-002",
    )

    failed_record = runtime.fail(
        "execution-002",
        error_code="CODE_GENERATION_FAILED",
        error_message="Test failure.",
        step_name="generate_code",
    )

    if failed_record.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    failed_observation = (
        runtime.get_observation(
            "execution-002"
        )
    )

    if failed_observation is None:
        raise RuntimeError(
            "Failed observation should exist."
        )

    if failed_observation.status != (
        "failed"
    ):
        raise RuntimeError(
            "Observer should report failed."
        )

    failed_audit = runtime.get_audit(
        "execution-002"
    )

    failed_types = [
        record.event_type
        for record in failed_audit
    ]

    if (
        "execution.failed"
        not in failed_types
    ):
        raise RuntimeError(
            "Failed event should be audited."
        )

    print("FAILURE RUNTIME: PASS")

    # -------------------------------------------------
    # CANCEL EXECUTION
    # -------------------------------------------------

    runtime.start(
        "execution-003",
        task_id="task-003",
        total_steps=1,
    )

    cancelled_record = runtime.cancel(
        "execution-003"
    )

    if cancelled_record.status != (
        "cancelled"
    ):
        raise RuntimeError(
            "Execution should be cancelled."
        )

    cancelled_observation = (
        runtime.get_observation(
            "execution-003"
        )
    )

    if cancelled_observation is None:
        raise RuntimeError(
            "Cancelled observation should exist."
        )

    if cancelled_observation.status != (
        "cancelled"
    ):
        raise RuntimeError(
            "Observer should report cancelled."
        )

    cancelled_audit = runtime.get_audit(
        "execution-003"
    )

    cancelled_types = [
        record.event_type
        for record in cancelled_audit
    ]

    if (
        "execution.cancelled"
        not in cancelled_types
    ):
        raise RuntimeError(
            "Cancelled event should be audited."
        )

    print("CANCEL RUNTIME: PASS")

    # -------------------------------------------------
    # AUDIT COUNT
    # -------------------------------------------------

    if runtime.audit_count() <= 0:
        raise RuntimeError(
            "Runtime should contain audit records."
        )

    print(
        "TOTAL AUDIT RECORDS:",
        runtime.audit_count(),
    )

    print("AUDIT COUNT: PASS")

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    runtime.close()

    print("CLOSE: PASS")

    print()
    print("=" * 60)
    print("EXECUTION RUNTIME: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()