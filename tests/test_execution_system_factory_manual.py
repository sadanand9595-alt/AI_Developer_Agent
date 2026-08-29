from core.execution_system import ExecutionSystem
from core.execution_system_factory import (
    ExecutionSystemFactory,
)


def main() -> None:
    # -------------------------------------------------
    # FACTORY CREATE
    # -------------------------------------------------

    system = ExecutionSystemFactory.create()

    if not isinstance(
        system,
        ExecutionSystem,
    ):
        raise RuntimeError(
            "Factory must return ExecutionSystem."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    record = system.start(
        "factory-system-001",
        task_id="factory-task-001",
        total_steps=2,
        metadata={
            "source": "factory-system-test",
        },
    )

    if record.execution_id != "factory-system-001":
        raise RuntimeError(
            "Execution ID is incorrect."
        )

    if record.status != "running":
        raise RuntimeError(
            "Execution should be running."
        )

    if not system.is_registered(
        "factory-system-001"
    ):
        raise RuntimeError(
            "Execution should be registered."
        )

    print("START: PASS")
    print("REGISTRATION: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    system.start_step(
        "factory-system-001",
        "analyze",
        task_id="factory-task-001",
    )

    system.complete_step(
        "factory-system-001",
        "analyze",
        task_id="factory-task-001",
    )

    progress = system.get_progress(
        "factory-system-001"
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
        "factory-system-001",
        "generate",
        task_id="factory-task-001",
    )

    system.complete_step(
        "factory-system-001",
        "generate",
        task_id="factory-task-001",
    )

    progress = system.get_progress(
        "factory-system-001"
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
    # AUTO UNREGISTER
    # -------------------------------------------------

    if system.is_registered(
        "factory-system-001"
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
        "factory-system-001"
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
        "factory-system-001"
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
    # FACTORY ISOLATION
    # -------------------------------------------------

    second_system = (
        ExecutionSystemFactory.create()
    )

    if second_system.get(
        "factory-system-001"
    ) is not None:
        raise RuntimeError(
            "Factory instances must be isolated."
        )

    if second_system.registered_count() != 0:
        raise RuntimeError(
            "Second system registry must start empty."
        )

    if second_system.audit_count() != 0:
        raise RuntimeError(
            "Second system audit must start empty."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # FAILURE
    # -------------------------------------------------

    system.start(
        "factory-system-002",
        task_id="factory-task-002",
        total_steps=1,
    )

    failed = system.fail(
        "factory-system-002",
        error_code="FACTORY_TEST_FAILURE",
        error_message="Factory failure test.",
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    if system.is_registered(
        "factory-system-002"
    ):
        raise RuntimeError(
            "Failed execution should be unregistered."
        )

    print("FAILURE: PASS")

    # -------------------------------------------------
    # CANCEL
    # -------------------------------------------------

    system.start(
        "factory-system-003",
        task_id="factory-task-003",
        total_steps=1,
    )

    cancelled = system.cancel(
        "factory-system-003"
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    if system.is_registered(
        "factory-system-003"
    ):
        raise RuntimeError(
            "Cancelled execution should be unregistered."
        )

    print("CANCEL: PASS")

    # -------------------------------------------------
    # COUNTERS
    # -------------------------------------------------

    if system.active_count() != 0:
        raise RuntimeError(
            "No terminal execution should remain active."
        )

    if system.registered_count() != 0:
        raise RuntimeError(
            "No terminal execution should remain registered."
        )

    if system.audit_count() <= 0:
        raise RuntimeError(
            "Audit records should exist."
        )

    print("ACTIVE COUNT: PASS")
    print("REGISTERED COUNT: PASS")
    print(
        "AUDIT COUNT:",
        system.audit_count(),
    )
    print("AUDIT COUNT: PASS")

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    system.close()
    second_system.close()

    print("CLOSE: PASS")

    print()
    print("=" * 60)
    print("EXECUTION SYSTEM FACTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()