from core.execution_bootstrap import ExecutionBootstrap
from core.execution_system import ExecutionSystem
from core.execution_system_factory import ExecutionSystemFactory


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
    # RESTART FAILURE LEAVES NO STALE STATE
    # -------------------------------------------------
    #
    # If ExecutionSystemFactory.create() fails during
    # restart() after the old system was already closed,
    # the bootstrap must be left honestly uninitialized
    # (None), not pointing at the stale closed system.
    # -------------------------------------------------

    failure_bootstrap = ExecutionBootstrap()
    system_before_failure = failure_bootstrap.initialize()

    original_create = ExecutionSystemFactory.create

    def failing_create():
        raise RuntimeError("simulated construction failure")

    ExecutionSystemFactory.create = staticmethod(
        failing_create
    )

    try:
        failure_bootstrap.restart()
    except RuntimeError:
        pass
    else:
        raise RuntimeError(
            "restart() should propagate the factory failure."
        )
    finally:
        ExecutionSystemFactory.create = original_create

    if failure_bootstrap.is_initialized():
        raise RuntimeError(
            "is_initialized() must be False after a failed "
            "restart(), not report the stale closed system."
        )

    if failure_bootstrap.get() is not None:
        raise RuntimeError(
            "get() must return None after a failed restart(), "
            "not the stale closed system."
        )

    recovered_system = failure_bootstrap.initialize()

    if recovered_system is system_before_failure:
        raise RuntimeError(
            "Recovery after a failed restart() should produce "
            "a fresh system."
        )

    failure_bootstrap.shutdown()

    print("RESTART FAILURE LEAVES NO STALE STATE: PASS")

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