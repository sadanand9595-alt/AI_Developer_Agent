from core.execution_facade import ExecutionFacade


def main() -> None:
    facade = ExecutionFacade()

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    record = facade.start(
        "facade-execution-001",
        task_id="facade-task-001",
        total_steps=2,
        metadata={
            "source": "facade-test",
        },
    )

    if record.execution_id != (
        "facade-execution-001"
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

    facade.start_step(
        "facade-execution-001",
        "analyze",
        task_id="facade-task-001",
    )

    facade.complete_step(
        "facade-execution-001",
        "analyze",
        task_id="facade-task-001",
    )

    progress = facade.get_progress(
        "facade-execution-001"
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

    facade.start_step(
        "facade-execution-001",
        "generate",
        task_id="facade-task-001",
    )

    facade.complete_step(
        "facade-execution-001",
        "generate",
        task_id="facade-task-001",
    )

    progress = facade.get_progress(
        "facade-execution-001"
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

    completed = facade.get(
        "facade-execution-001"
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
    # OBSERVATION
    # -------------------------------------------------

    observation = facade.get_observation(
        "facade-execution-001"
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

    audit = facade.get_audit(
        "facade-execution-001"
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

    facade.start(
        "facade-execution-002",
        task_id="facade-task-002",
        total_steps=1,
    )

    facade.start_step(
        "facade-execution-002",
        "generate_code",
        task_id="facade-task-002",
    )

    failed = facade.fail(
        "facade-execution-002",
        error_code="GENERATION_FAILED",
        error_message="Facade test failure.",
        step_name="generate_code",
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    failed_observation = facade.get_observation(
        "facade-execution-002"
    )

    if failed_observation is None:
        raise RuntimeError(
            "Failed observation should exist."
        )

    if failed_observation.status != "failed":
        raise RuntimeError(
            "Observer should report failed."
        )

    print("FAILURE: PASS")

    # -------------------------------------------------
    # CANCEL
    # -------------------------------------------------

    facade.start(
        "facade-execution-003",
        task_id="facade-task-003",
        total_steps=1,
    )

    cancelled = facade.cancel(
        "facade-execution-003"
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    cancelled_observation = (
        facade.get_observation(
            "facade-execution-003"
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

    print("CANCEL: PASS")

    # -------------------------------------------------
    # ACTIVE COUNT
    # -------------------------------------------------

    if facade.active_count() != 0:
        raise RuntimeError(
            "No completed/failed/cancelled execution "
            "should remain active."
        )

    print("ACTIVE COUNT: PASS")

    # -------------------------------------------------
    # AUDIT COUNT
    # -------------------------------------------------

    if facade.audit_count() <= 0:
        raise RuntimeError(
            "Audit count should be greater than zero."
        )

    print(
        "AUDIT COUNT:",
        facade.audit_count(),
    )

    print("AUDIT COUNT: PASS")

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    facade.close()

    print("CLOSE: PASS")

    print()
    print("=" * 60)
    print("EXECUTION FACADE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()