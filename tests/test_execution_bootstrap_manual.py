from core.execution_bootstrap import ExecutionBootstrap
from core.execution_system import ExecutionSystem


def main() -> None:
    bootstrap = ExecutionBootstrap()

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if bootstrap.is_initialized():
        raise RuntimeError(
            "Bootstrap must start uninitialized."
        )

    if bootstrap.get() is not None:
        raise RuntimeError(
            "System must not exist before initialization."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # INITIALIZE
    # -------------------------------------------------

    system = bootstrap.initialize()

    if not isinstance(
        system,
        ExecutionSystem,
    ):
        raise RuntimeError(
            "initialize() must return ExecutionSystem."
        )

    if not bootstrap.is_initialized():
        raise RuntimeError(
            "Bootstrap should be initialized."
        )

    if bootstrap.get() is not system:
        raise RuntimeError(
            "get() must return the initialized system."
        )

    print("INITIALIZE: PASS")

    # -------------------------------------------------
    # IDEMPOTENT INITIALIZATION
    # -------------------------------------------------

    same_system = bootstrap.initialize()

    if same_system is not system:
        raise RuntimeError(
            "Repeated initialize() must return "
            "the same system instance."
        )

    print("IDEMPOTENT INITIALIZE: PASS")

    # -------------------------------------------------
    # USE SYSTEM
    # -------------------------------------------------

    record = system.start(
        "bootstrap-execution-001",
        task_id="bootstrap-task-001",
        total_steps=1,
        metadata={
            "source": "bootstrap-test",
        },
    )

    if record.status != "running":
        raise RuntimeError(
            "Execution should be running."
        )

    system.start_step(
        "bootstrap-execution-001",
        "execute",
        task_id="bootstrap-task-001",
    )

    system.complete_step(
        "bootstrap-execution-001",
        "execute",
        task_id="bootstrap-task-001",
    )

    progress = system.get_progress(
        "bootstrap-execution-001"
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

    print("SYSTEM OPERATION: PASS")

    # -------------------------------------------------
    # SHUTDOWN
    # -------------------------------------------------

    bootstrap.shutdown()

    if bootstrap.is_initialized():
        raise RuntimeError(
            "Bootstrap should be uninitialized after shutdown."
        )

    if bootstrap.get() is not None:
        raise RuntimeError(
            "System reference should be released."
        )

    print("SHUTDOWN: PASS")

    # -------------------------------------------------
    # REPEATED SHUTDOWN
    # -------------------------------------------------

    bootstrap.shutdown()

    if bootstrap.is_initialized():
        raise RuntimeError(
            "Repeated shutdown must remain safe."
        )

    print("IDEMPOTENT SHUTDOWN: PASS")

    # -------------------------------------------------
    # RESTART
    # -------------------------------------------------

    restarted = bootstrap.restart()

    if not isinstance(
        restarted,
        ExecutionSystem,
    ):
        raise RuntimeError(
            "restart() must return ExecutionSystem."
        )

    if not bootstrap.is_initialized():
        raise RuntimeError(
            "Bootstrap should be initialized after restart."
        )

    if bootstrap.get() is not restarted:
        raise RuntimeError(
            "get() should return restarted system."
        )

    print("RESTART: PASS")

    # -------------------------------------------------
    # RESTART ISOLATION
    # -------------------------------------------------

    if restarted.get(
        "bootstrap-execution-001"
    ) is not None:
        raise RuntimeError(
            "Restarted system must not retain old execution state."
        )

    if restarted.registered_count() != 0:
        raise RuntimeError(
            "Restarted registry must be empty."
        )

    if restarted.audit_count() != 0:
        raise RuntimeError(
            "Restarted audit must be empty."
        )

    print("RESTART ISOLATION: PASS")

    # -------------------------------------------------
    # SECOND OPERATION
    # -------------------------------------------------

    record = restarted.start(
        "bootstrap-execution-002",
        task_id="bootstrap-task-002",
        total_steps=1,
    )

    if record.status != "running":
        raise RuntimeError(
            "Restarted system should be operational."
        )

    restarted.cancel(
        "bootstrap-execution-002"
    )

    if restarted.get(
        "bootstrap-execution-002"
    ) is None:
        raise RuntimeError(
            "Cancelled execution record should remain queryable."
        )

    print("RESTARTED SYSTEM OPERATION: PASS")

    # -------------------------------------------------
    # FINAL SHUTDOWN
    # -------------------------------------------------

    bootstrap.shutdown()

    if bootstrap.is_initialized():
        raise RuntimeError(
            "Final shutdown failed."
        )

    print("FINAL SHUTDOWN: PASS")

    print()
    print("=" * 60)
    print("EXECUTION BOOTSTRAP: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()