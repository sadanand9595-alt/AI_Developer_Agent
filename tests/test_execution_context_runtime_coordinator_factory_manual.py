from core.execution_context_runtime_coordinator import (
    ExecutionContextRuntimeCoordinator,
)
from core.execution_context_runtime_coordinator_factory import (
    ExecutionContextRuntimeCoordinatorFactory,
)


def main() -> None:
    # -------------------------------------------------
    # FACTORY CREATE
    # -------------------------------------------------

    coordinator = (
        ExecutionContextRuntimeCoordinatorFactory.create()
    )

    if not isinstance(
        coordinator,
        ExecutionContextRuntimeCoordinator,
    ):
        raise RuntimeError(
            "Factory must return ExecutionContextRuntimeCoordinator."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if coordinator.count() != 0:
        raise RuntimeError(
            "Factory-created coordinator must start empty."
        )

    if coordinator.ids():
        raise RuntimeError(
            "Factory-created coordinator must have no IDs."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE RUNTIME
    # -------------------------------------------------

    runtime = coordinator.create(
        "factory-runtime-coordinator-001"
    )

    if runtime.context_id != (
        "factory-runtime-coordinator-001"
    ):
        raise RuntimeError(
            "Runtime context ID is incorrect."
        )

    if not runtime.active:
        raise RuntimeError(
            "New runtime must be active."
        )

    if coordinator.count() != 1:
        raise RuntimeError(
            "Expected one runtime."
        )

    print("CREATE RUNTIME: PASS")

    # -------------------------------------------------
    # RUNTIME OPERATIONS
    # -------------------------------------------------

    coordinator.start_step(
        "factory-runtime-coordinator-001",
        "execute",
    )

    coordinator.complete_step(
        "factory-runtime-coordinator-001"
    )

    coordinator.set_variable(
        "factory-runtime-coordinator-001",
        "status",
        "running",
    )

    if coordinator.get_variable(
        "factory-runtime-coordinator-001",
        "status",
    ) != "running":
        raise RuntimeError(
            "Runtime variable operation failed."
        )

    print("RUNTIME OPERATIONS: PASS")

    # -------------------------------------------------
    # SNAPSHOT
    # -------------------------------------------------

    snapshot = coordinator.snapshot(
        "factory-runtime-coordinator-001"
    )

    if snapshot["context_id"] != (
        "factory-runtime-coordinator-001"
    ):
        raise RuntimeError(
            "Snapshot context ID is incorrect."
        )

    if snapshot["completed_steps"] != 1:
        raise RuntimeError(
            "Snapshot completed steps are incorrect."
        )

    if snapshot["variables"].get(
        "status"
    ) != "running":
        raise RuntimeError(
            "Snapshot variables are incorrect."
        )

    print("SNAPSHOT: PASS")

    # -------------------------------------------------
    # FACTORY ISOLATION
    # -------------------------------------------------

    second = (
        ExecutionContextRuntimeCoordinatorFactory.create()
    )

    if second.count() != 0:
        raise RuntimeError(
            "Factory instances must be isolated."
        )

    if second.get(
        "factory-runtime-coordinator-001"
    ) is not None:
        raise RuntimeError(
            "Runtime leaked into second factory instance."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # SECOND INSTANCE
    # -------------------------------------------------

    second_runtime = second.create(
        "factory-runtime-coordinator-002"
    )

    if second.count() != 1:
        raise RuntimeError(
            "Second coordinator should contain one runtime."
        )

    if coordinator.count() != 1:
        raise RuntimeError(
            "First coordinator must remain unchanged."
        )

    print("SECOND INSTANCE: PASS")

    # -------------------------------------------------
    # STOP ISOLATION
    # -------------------------------------------------

    if not coordinator.stop(
        "factory-runtime-coordinator-001"
    ):
        raise RuntimeError(
            "First runtime should stop."
        )

    if runtime.active:
        raise RuntimeError(
            "First runtime must be inactive."
        )

    if not second_runtime.active:
        raise RuntimeError(
            "Second runtime must remain active."
        )

    print("STOP ISOLATION: PASS")

    # -------------------------------------------------
    # CLEAR SECOND
    # -------------------------------------------------

    cleared = second.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one runtime to be cleared."
        )

    if second.count() != 0:
        raise RuntimeError(
            "Second coordinator should be empty."
        )

    if second_runtime.active:
        raise RuntimeError(
            "Clear should stop the runtime."
        )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT RUNTIME COORDINATOR FACTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()