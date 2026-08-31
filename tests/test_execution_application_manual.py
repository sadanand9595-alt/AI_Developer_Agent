from core.execution_application import ExecutionApplication
from core.execution_system import ExecutionSystem


def main() -> None:
    application = ExecutionApplication()

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if application.is_running():
        raise RuntimeError(
            "Application must start stopped."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # SYSTEM BEFORE START
    # -------------------------------------------------

    try:
        application.system()
    except RuntimeError:
        print("PRE-START PROTECTION: PASS")
    else:
        raise RuntimeError(
            "system() must reject access before start."
        )

    # -------------------------------------------------
    # START APPLICATION
    # -------------------------------------------------

    system = application.start()

    if not isinstance(
        system,
        ExecutionSystem,
    ):
        raise RuntimeError(
            "start() must return ExecutionSystem."
        )

    if not application.is_running():
        raise RuntimeError(
            "Application should be running."
        )

    if application.system() is not system:
        raise RuntimeError(
            "system() should return active system."
        )

    print("START: PASS")

    # -------------------------------------------------
    # START EXECUTION
    # -------------------------------------------------

    record = application.start_execution(
        "application-execution-001",
        task_id="application-task-001",
        total_steps=2,
        metadata={
            "source": "application-test",
        },
    )

    if record.execution_id != (
        "application-execution-001"
    ):
        raise RuntimeError(
            "Execution ID is incorrect."
        )

    if record.status != "running":
        raise RuntimeError(
            "Execution should be running."
        )

    if application.registered_count() != 1:
        raise RuntimeError(
            "Execution should be registered."
        )

    print("START EXECUTION: PASS")
    print("REGISTRATION: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    application.start_step(
        "application-execution-001",
        "analyze",
        task_id="application-task-001",
    )

    application.complete_step(
        "application-execution-001",
        "analyze",
        task_id="application-task-001",
    )

    progress = application.get_progress(
        "application-execution-001"
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

    application.start_step(
        "application-execution-001",
        "generate",
        task_id="application-task-001",
    )

    application.complete_step(
        "application-execution-001",
        "generate",
        task_id="application-task-001",
    )

    progress = application.get_progress(
        "application-execution-001"
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

    print("COMPLETION: PASS")

    # -------------------------------------------------
    # STATE + OBSERVATION
    # -------------------------------------------------

    completed = application.get(
        "application-execution-001"
    )

    if completed is None:
        raise RuntimeError(
            "Execution record should exist."
        )

    if completed.status != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    observation = application.get_observation(
        "application-execution-001"
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

    print("STATE: PASS")
    print("OBSERVATION: PASS")

    # -------------------------------------------------
    # AUTO UNREGISTER
    # -------------------------------------------------

    if application.registered_count() != 0:
        raise RuntimeError(
            "Completed execution should be unregistered."
        )

    print("AUTO UNREGISTER: PASS")

    # -------------------------------------------------
    # AUDIT
    # -------------------------------------------------

    audit = application.get_audit(
        "application-execution-001"
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

    print("AUDIT: PASS")

    # -------------------------------------------------
    # FAILURE
    # -------------------------------------------------

    application.start_execution(
        "application-execution-002",
        task_id="application-task-002",
        total_steps=1,
    )

    failed = application.fail(
        "application-execution-002",
        error_code="APPLICATION_TEST_FAILURE",
        error_message="Application failure test.",
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    if application.registered_count() != 0:
        raise RuntimeError(
            "Failed execution should be unregistered."
        )

    print("FAILURE: PASS")

    # -------------------------------------------------
    # CANCEL
    # -------------------------------------------------

    application.start_execution(
        "application-execution-003",
        task_id="application-task-003",
        total_steps=1,
    )

    cancelled = application.cancel(
        "application-execution-003"
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    if application.registered_count() != 0:
        raise RuntimeError(
            "Cancelled execution should be unregistered."
        )

    print("CANCEL: PASS")

    # -------------------------------------------------
    # COUNTERS
    # -------------------------------------------------

    if application.active_count() != 0:
        raise RuntimeError(
            "No terminal execution should remain active."
        )

    if application.registered_count() != 0:
        raise RuntimeError(
            "No terminal execution should remain registered."
        )

    if application.audit_count() <= 0:
        raise RuntimeError(
            "Audit records should exist."
        )

    print("ACTIVE COUNT: PASS")
    print("REGISTERED COUNT: PASS")
    print(
        "AUDIT COUNT:",
        application.audit_count(),
    )
    print("AUDIT COUNT: PASS")

    # -------------------------------------------------
    # STOP
    # -------------------------------------------------

    application.stop()

    if application.is_running():
        raise RuntimeError(
            "Application should be stopped."
        )

    print("STOP: PASS")

    # -------------------------------------------------
    # RESTART
    # -------------------------------------------------

    restarted = application.restart()

    if not isinstance(
        restarted,
        ExecutionSystem,
    ):
        raise RuntimeError(
            "restart() must return ExecutionSystem."
        )

    if not application.is_running():
        raise RuntimeError(
            "Application should be running after restart."
        )

    if application.registered_count() != 0:
        raise RuntimeError(
            "Restarted registry must be empty."
        )

    if application.audit_count() != 0:
        raise RuntimeError(
            "Restarted audit must be empty."
        )

    if restarted.get(
        "application-execution-001"
    ) is not None:
        raise RuntimeError(
            "Old execution state must not survive restart."
        )

    print("RESTART: PASS")
    print("RESTART ISOLATION: PASS")

    # -------------------------------------------------
    # FINAL STOP
    # -------------------------------------------------

    application.stop()

    if application.is_running():
        raise RuntimeError(
            "Final stop failed."
        )

    print("FINAL STOP: PASS")

    for bad_bootstrap in ("not-a-bootstrap", 123):
        try:
            ExecutionApplication(bootstrap=bad_bootstrap)
        except TypeError:
            pass
        else:
            raise RuntimeError(
                f"Invalid bootstrap {bad_bootstrap!r} should "
                "be rejected."
            )

    print("INVALID BOOTSTRAP DEPENDENCY: PASS")

    print()
    print("=" * 60)
    print("EXECUTION APPLICATION: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()