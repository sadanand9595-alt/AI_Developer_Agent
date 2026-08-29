from core.execution_application import ExecutionApplication
from core.execution_application_factory import (
    ExecutionApplicationFactory,
)


def main() -> None:
    # -------------------------------------------------
    # FACTORY CREATE
    # -------------------------------------------------

    application = (
        ExecutionApplicationFactory.create()
    )

    if not isinstance(
        application,
        ExecutionApplication,
    ):
        raise RuntimeError(
            "Factory must return ExecutionApplication."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if application.is_running():
        raise RuntimeError(
            "Application should initially be stopped."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    system = application.start()

    if not application.is_running():
        raise RuntimeError(
            "Application should be running."
        )

    if application.system() is not system:
        raise RuntimeError(
            "system() should return the active system."
        )

    print("START: PASS")

    # -------------------------------------------------
    # EXECUTION
    # -------------------------------------------------

    record = application.start_execution(
        "factory-app-001",
        task_id="factory-app-task-001",
        total_steps=1,
        metadata={
            "source": "factory-application-test",
        },
    )

    if record.status != "running":
        raise RuntimeError(
            "Execution should be running."
        )

    application.start_step(
        "factory-app-001",
        "execute",
        task_id="factory-app-task-001",
    )

    application.complete_step(
        "factory-app-001",
        "execute",
        task_id="factory-app-task-001",
    )

    progress = application.get_progress(
        "factory-app-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.progress_percent != 100.0:
        raise RuntimeError(
            "Progress should reach 100%."
        )

    if progress.status != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    print("EXECUTION: PASS")

    # -------------------------------------------------
    # AUDIT
    # -------------------------------------------------

    audit = application.get_audit(
        "factory-app-001"
    )

    if not audit:
        raise RuntimeError(
            "Audit records should exist."
        )

    print("AUDIT: PASS")

    # -------------------------------------------------
    # ISOLATION
    # -------------------------------------------------

    application.stop()

    second_application = (
        ExecutionApplicationFactory.create()
    )

    if second_application.is_running():
        raise RuntimeError(
            "New factory instance must start stopped."
        )

    second_application.start()

    if second_application.get(
        "factory-app-001"
    ) is not None:
        raise RuntimeError(
            "Factory instances must have isolated state."
        )

    if second_application.registered_count() != 0:
        raise RuntimeError(
            "New registry must be empty."
        )

    if second_application.audit_count() != 0:
        raise RuntimeError(
            "New audit must be empty."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # RESTART
    # -------------------------------------------------

    restarted = second_application.restart()

    if not second_application.is_running():
        raise RuntimeError(
            "Application should be running after restart."
        )

    if restarted is not second_application.system():
        raise RuntimeError(
            "Restarted system should be active."
        )

    if second_application.registered_count() != 0:
        raise RuntimeError(
            "Restarted registry must be empty."
        )

    if second_application.audit_count() != 0:
        raise RuntimeError(
            "Restarted audit must be empty."
        )

    print("RESTART: PASS")
    print("RESTART ISOLATION: PASS")

    # -------------------------------------------------
    # FINAL STOP
    # -------------------------------------------------

    second_application.stop()

    if second_application.is_running():
        raise RuntimeError(
            "Final stop failed."
        )

    print("STOP: PASS")

    print()
    print("=" * 60)
    print("EXECUTION APPLICATION FACTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()