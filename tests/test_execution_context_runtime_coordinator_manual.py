from core.execution_context_runtime import (
    ExecutionContextRuntime,
)
from core.execution_context_runtime_coordinator import (
    ExecutionContextRuntimeCoordinator,
)


def main() -> None:
    coordinator = ExecutionContextRuntimeCoordinator()

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if coordinator.count() != 0:
        raise RuntimeError(
            "Coordinator must start empty."
        )

    if coordinator.ids():
        raise RuntimeError(
            "Runtime IDs must initially be empty."
        )

    if coordinator.all():
        raise RuntimeError(
            "Runtime collection must initially be empty."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    runtime = coordinator.create(
        "runtime-coordinator-001"
    )

    if not isinstance(
        runtime,
        ExecutionContextRuntime,
    ):
        raise RuntimeError(
            "create() must return ExecutionContextRuntime."
        )

    if coordinator.count() != 1:
        raise RuntimeError(
            "Expected one runtime."
        )

    if not coordinator.contains(
        "runtime-coordinator-001"
    ):
        raise RuntimeError(
            "Created runtime should exist."
        )

    print("CREATE: PASS")

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    found = coordinator.get(
        "runtime-coordinator-001"
    )

    if found is not runtime:
        raise RuntimeError(
            "get() returned incorrect runtime."
        )

    print("GET: PASS")

    # -------------------------------------------------
    # START STEP
    # -------------------------------------------------

    result = coordinator.start_step(
        "runtime-coordinator-001",
        "analyze",
    )

    if result is not runtime:
        raise RuntimeError(
            "start_step() should return the runtime."
        )

    if runtime.current_step != "analyze":
        raise RuntimeError(
            "Current step was not set."
        )

    print("START STEP: PASS")

    # -------------------------------------------------
    # COMPLETE STEP
    # -------------------------------------------------

    result = coordinator.complete_step(
        "runtime-coordinator-001"
    )

    if result is not runtime:
        raise RuntimeError(
            "complete_step() should return the runtime."
        )

    if runtime.completed_steps != 1:
        raise RuntimeError(
            "Completed step count should be one."
        )

    print("COMPLETE STEP: PASS")

    # -------------------------------------------------
    # FAIL STEP
    # -------------------------------------------------

    coordinator.start_step(
        "runtime-coordinator-001",
        "validate",
    )

    result = coordinator.fail_step(
        "runtime-coordinator-001"
    )

    if result is not runtime:
        raise RuntimeError(
            "fail_step() should return the runtime."
        )

    if runtime.failed_steps != 1:
        raise RuntimeError(
            "Failed step count should be one."
        )

    print("FAIL STEP: PASS")

    # -------------------------------------------------
    # VARIABLES
    # -------------------------------------------------

    coordinator.set_variable(
        "runtime-coordinator-001",
        "attempt",
        1,
    )

    coordinator.set_variable(
        "runtime-coordinator-001",
        "status",
        "running",
    )

    if coordinator.get_variable(
        "runtime-coordinator-001",
        "attempt",
    ) != 1:
        raise RuntimeError(
            "Variable value is incorrect."
        )

    if coordinator.get_variable(
        "runtime-coordinator-001",
        "missing",
        "default",
    ) != "default":
        raise RuntimeError(
            "Variable default is incorrect."
        )

    print("SET/GET VARIABLES: PASS")

    # -------------------------------------------------
    # REMOVE VARIABLE
    # -------------------------------------------------

    removed = coordinator.remove_variable(
        "runtime-coordinator-001",
        "attempt",
    )

    if not removed:
        raise RuntimeError(
            "Existing variable should be removed."
        )

    if coordinator.get_variable(
        "runtime-coordinator-001",
        "attempt",
    ) is not None:
        raise RuntimeError(
            "Removed variable must not exist."
        )

    print("REMOVE VARIABLE: PASS")

    # -------------------------------------------------
    # PAUSE
    # -------------------------------------------------

    result = coordinator.pause(
        "runtime-coordinator-001"
    )

    if result is not runtime:
        raise RuntimeError(
            "pause() should return the runtime."
        )

    if not runtime.paused:
        raise RuntimeError(
            "Runtime should be paused."
        )

    print("PAUSE: PASS")

    # -------------------------------------------------
    # RESUME
    # -------------------------------------------------

    result = coordinator.resume(
        "runtime-coordinator-001"
    )

    if result is not runtime:
        raise RuntimeError(
            "resume() should return the runtime."
        )

    if runtime.paused:
        raise RuntimeError(
            "Runtime should be resumed."
        )

    print("RESUME: PASS")

    # -------------------------------------------------
    # SNAPSHOT
    # -------------------------------------------------

    snapshot = coordinator.snapshot(
        "runtime-coordinator-001"
    )

    if snapshot["context_id"] != (
        "runtime-coordinator-001"
    ):
        raise RuntimeError(
            "Snapshot context ID is incorrect."
        )

    if snapshot["completed_steps"] != 1:
        raise RuntimeError(
            "Snapshot completed steps are incorrect."
        )

    if snapshot["failed_steps"] != 1:
        raise RuntimeError(
            "Snapshot failed steps are incorrect."
        )

    if snapshot["variables"].get(
        "status"
    ) != "running":
        raise RuntimeError(
            "Snapshot variables are incorrect."
        )

    print("SNAPSHOT: PASS")

    # -------------------------------------------------
    # REGISTER EXISTING
    # -------------------------------------------------

    external = ExecutionContextRuntime(
        context_id="runtime-coordinator-002"
    )

    coordinator.register(
        external
    )

    if coordinator.count() != 2:
        raise RuntimeError(
            "Expected two runtimes."
        )

    print("REGISTER EXISTING: PASS")

    # -------------------------------------------------
    # ALL / IDS
    # -------------------------------------------------

    ids = coordinator.ids()

    if set(ids) != {
        "runtime-coordinator-001",
        "runtime-coordinator-002",
    }:
        raise RuntimeError(
            "Runtime IDs are incorrect."
        )

    runtimes = coordinator.all()

    if len(runtimes) != 2:
        raise RuntimeError(
            "all() should return two runtimes."
        )

    if runtime not in runtimes:
        raise RuntimeError(
            "Primary runtime missing."
        )

    if external not in runtimes:
        raise RuntimeError(
            "External runtime missing."
        )

    print("IDS / ALL: PASS")

    # -------------------------------------------------
    # MISSING RUNTIME
    # -------------------------------------------------

    try:
        coordinator.start_step(
            "missing-runtime",
            "test",
        )
    except KeyError:
        print("MISSING RUNTIME: PASS")
    else:
        raise RuntimeError(
            "Missing runtime should raise KeyError."
        )

    # -------------------------------------------------
    # STOP
    # -------------------------------------------------

    stopped = coordinator.stop(
        "runtime-coordinator-001"
    )

    if not stopped:
        raise RuntimeError(
            "Runtime should stop."
        )

    if runtime.active:
        raise RuntimeError(
            "Runtime must be inactive."
        )

    if external.active is not True:
        raise RuntimeError(
            "External runtime must remain active."
        )

    print("STOP: PASS")

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    removed = coordinator.unregister(
        "runtime-coordinator-001"
    )

    if not removed:
        raise RuntimeError(
            "Runtime should be unregistered."
        )

    if coordinator.contains(
        "runtime-coordinator-001"
    ):
        raise RuntimeError(
            "Unregistered runtime must not remain."
        )

    if coordinator.count() != 1:
        raise RuntimeError(
            "One runtime should remain."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNREGISTER WITHOUT STOP
    # -------------------------------------------------

    removed = coordinator.unregister(
        "runtime-coordinator-002",
        stop=False,
    )

    if not removed:
        raise RuntimeError(
            "External runtime should be unregistered."
        )

    if not external.active:
        raise RuntimeError(
            "stop=False must preserve active state."
        )

    print("UNREGISTER WITHOUT STOP: PASS")

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    coordinator.create(
        "runtime-coordinator-003"
    )

    coordinator.create(
        "runtime-coordinator-004"
    )

    if coordinator.count() != 2:
        raise RuntimeError(
            "Expected two runtimes before clear."
        )

    cleared = coordinator.clear()

    if cleared != 2:
        raise RuntimeError(
            "Expected two runtimes to be cleared."
        )

    if coordinator.count() != 0:
        raise RuntimeError(
            "Coordinator should be empty after clear."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT RUNTIME COORDINATOR: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()