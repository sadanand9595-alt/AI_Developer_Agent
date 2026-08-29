from core.execution_system import ExecutionSystem


def main() -> None:
    system = ExecutionSystem()

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    record = system.start(
        "system-execution-001",
        task_id="system-task-001",
        total_steps=2,
        metadata={
            "source": "system-test",
        },
    )

    if record.execution_id != "system-execution-001":
        raise RuntimeError(
            "Execution ID is incorrect."
        )

    if record.status != "running":
        raise RuntimeError(
            "Execution should be running."
        )

    if not system.is_registered(
        "system-execution-001"
    ):
        raise RuntimeError(
            "Execution should be registered."
        )

    if system.registered_count() != 1:
        raise RuntimeError(
            "Expected one registered execution."
        )

    print("START: PASS")
    print("REGISTRATION: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    system.start_step(
        "system-execution-001",
        "analyze",
        task_id="system-task-001",
    )

    system.complete_step(
        "system-execution-001",
        "analyze",
        task_id="system-task-001",
    )

    progress = system.get_progress(
        "system-execution-001"
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

    print(
        "STEP 1 PROGRESS:",
        progress.progress_percent,
    )

    print("STEP 1: PASS")

    # -------------------------------------------------
    # STEP 2
    # -------------------------------------------------

    system.start_step(
        "system-execution-001",
        "generate",
        task_id="system-task-001",
    )

    system.complete_step(
        "system-execution-001",
        "generate",
        task_id="system-task-001",
    )

    progress = system.get_progress(
        "system-execution-001"
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

    completed = system.get(
        "system-execution-001"
    )

    if completed is None:
        raise RuntimeError(
            "Execution record should exist."
        )

    if completed.status != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    print("EXECUTION STATE: PASS")

    # -------------------------------------------------
    # AUTO UNREGISTER
    # -------------------------------------------------

    if system.is_registered(
        "system-execution-001"
    ):
        raise RuntimeError(
            "Completed execution should be unregistered."
        )

    if system.registered_count() != 0:
        raise RuntimeError(
            "Registry should be empty."
        )

    print("AUTO UNREGISTER: PASS")

    # -------------------------------------------------
    # OBSERVATION
    # -------------------------------------------------

    observation = system.get_observation(
        "system-execution-001"
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

    audit = system.get_audit(
        "system-execution-001"
    )

    if not audit:
        raise RuntimeError(
            "Audit records should exist."
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

    print(
        "AUDIT EVENTS:",
        sorted(audit_types),
    )

    print("AUDIT: PASS")

    # -------------------------------------------------
    # FAILURE
    # -------------------------------------------------

    system.start(
        "system-execution-002",
        task_id="system-task-002",
        total_steps=1,
    )

    system.start_step(
        "system-execution-002",
        "generate_code",
        task_id="system-task-002",
    )

    failed = system.fail(
        "system-execution-002",
        error_code="GENERATION_FAILED",
        error_message="System test failure.",
        step_name="generate_code",
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    if system.is_registered(
        "system-execution-002"
    ):
        raise RuntimeError(
            "Failed execution should be unregistered."
        )

    failed_observation = (
        system.get_observation(
            "system-execution-002"
        )
    )

    if failed_observation is None:
        raise RuntimeError(
            "Failed observation should exist."
        )

    if failed_observation.status != "failed":
        raise RuntimeError(
            "Observer should report failed."
        )

    failed_audit = system.get_audit(
        "system-execution-002"
    )

    if not any(
        item.event_type == "execution.failed"
        for item in failed_audit
    ):
        raise RuntimeError(
            "Failure event should be audited."
        )

    print("FAILURE: PASS")

    # -------------------------------------------------
    # CANCEL
    # -------------------------------------------------

    system.start(
        "system-execution-003",
        task_id="system-task-003",
        total_steps=1,
    )

    cancelled = system.cancel(
        "system-execution-003"
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    if system.is_registered(
        "system-execution-003"
    ):
        raise RuntimeError(
            "Cancelled execution should be unregistered."
        )

    cancelled_observation = (
        system.get_observation(
            "system-execution-003"
        )
    )

    if cancelled_observation is None:
        raise RuntimeError(
            "Cancelled observation should exist."
        )

    if cancelled_observation.status != "cancelled":
        raise RuntimeError(
            "Observer should report cancelled."
        )

    cancelled_audit = system.get_audit(
        "system-execution-003"
    )

    if not any(
        item.event_type == "execution.cancelled"
        for item in cancelled_audit
    ):
        raise RuntimeError(
            "Cancellation event should be audited."
        )

    print("CANCEL: PASS")

    # -------------------------------------------------
    # GLOBAL COUNTERS
    # -------------------------------------------------

    if system.active_count() != 0:
        raise RuntimeError(
            "No terminal execution should remain active."
        )

    print("ACTIVE COUNT: PASS")

    if system.registered_count() != 0:
        raise RuntimeError(
            "No terminal execution should remain registered."
        )

    print("REGISTERED COUNT: PASS")

    if system.audit_count() <= 0:
        raise RuntimeError(
            "Audit records should exist."
        )

    print(
        "TOTAL AUDIT RECORDS:",
        system.audit_count(),
    )

    print("AUDIT COUNT: PASS")

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    system.close()

    print("CLOSE: PASS")

    print()
    print("=" * 60)
    print("EXECUTION SYSTEM: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()