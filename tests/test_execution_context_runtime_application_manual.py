from core.execution_context_runtime import (
    ExecutionContextRuntime,
)
from core.execution_context_runtime_application import (
    ExecutionContextRuntimeApplication,
)


def main() -> None:
    application = ExecutionContextRuntimeApplication()

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if application.count() != 0:
        raise RuntimeError(
            "Application must start empty."
        )

    if application.ids():
        raise RuntimeError(
            "Runtime IDs must initially be empty."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    runtime = application.create(
        "runtime-application-001"
    )

    if not isinstance(
        runtime,
        ExecutionContextRuntime,
    ):
        raise RuntimeError(
            "create() must return ExecutionContextRuntime."
        )

    if not runtime.active:
        raise RuntimeError(
            "New runtime must be active."
        )

    if application.count() != 1:
        raise RuntimeError(
            "Expected one runtime."
        )

    print("CREATE: PASS")

    # -------------------------------------------------
    # GET / CONTAINS
    # -------------------------------------------------

    if application.get(
        "runtime-application-001"
    ) is not runtime:
        raise RuntimeError(
            "get() returned incorrect runtime."
        )

    if not application.contains(
        "runtime-application-001"
    ):
        raise RuntimeError(
            "Runtime should exist."
        )

    if application.get(
        "missing-runtime"
    ) is not None:
        raise RuntimeError(
            "Missing runtime should return None."
        )

    print("GET / CONTAINS: PASS")

    # -------------------------------------------------
    # STEP LIFECYCLE
    # -------------------------------------------------

    result = application.start_step(
        "runtime-application-001",
        "analyze",
    )

    if result is not runtime:
        raise RuntimeError(
            "start_step() returned incorrect runtime."
        )

    if runtime.current_step != "analyze":
        raise RuntimeError(
            "Current step was not set."
        )

    application.complete_step(
        "runtime-application-001"
    )

    if runtime.completed_steps != 1:
        raise RuntimeError(
            "Completed step count should be one."
        )

    application.start_step(
        "runtime-application-001",
        "validate",
    )

    application.fail_step(
        "runtime-application-001"
    )

    if runtime.failed_steps != 1:
        raise RuntimeError(
            "Failed step count should be one."
        )

    print("STEP LIFECYCLE: PASS")

    # -------------------------------------------------
    # VARIABLES
    # -------------------------------------------------

    application.set_variable(
        "runtime-application-001",
        "status",
        "running",
    )

    application.set_variable(
        "runtime-application-001",
        "attempt",
        1,
    )

    if application.get_variable(
        "runtime-application-001",
        "status",
    ) != "running":
        raise RuntimeError(
            "Status variable is incorrect."
        )

    if application.get_variable(
        "runtime-application-001",
        "attempt",
    ) != 1:
        raise RuntimeError(
            "Attempt variable is incorrect."
        )

    if application.get_variable(
        "runtime-application-001",
        "missing",
        "default",
    ) != "default":
        raise RuntimeError(
            "Variable default is incorrect."
        )

    removed = application.remove_variable(
        "runtime-application-001",
        "attempt",
    )

    if not removed:
        raise RuntimeError(
            "Attempt variable should be removed."
        )

    if application.get_variable(
        "runtime-application-001",
        "attempt",
    ) is not None:
        raise RuntimeError(
            "Removed variable must not exist."
        )

    print("VARIABLES: PASS")

    # -------------------------------------------------
    # PAUSE / RESUME
    # -------------------------------------------------

    application.pause(
        "runtime-application-001"
    )

    if not runtime.paused:
        raise RuntimeError(
            "Runtime should be paused."
        )

    application.resume(
        "runtime-application-001"
    )

    if runtime.paused:
        raise RuntimeError(
            "Runtime should be resumed."
        )

    print("PAUSE / RESUME: PASS")

    # -------------------------------------------------
    # SNAPSHOT
    # -------------------------------------------------

    snapshot = application.snapshot(
        "runtime-application-001"
    )

    if snapshot["context_id"] != (
        "runtime-application-001"
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
            "Snapshot variable is incorrect."
        )

    print("SNAPSHOT: PASS")

    # -------------------------------------------------
    # REGISTER EXISTING
    # -------------------------------------------------

    external = ExecutionContextRuntime(
        context_id="runtime-application-002"
    )

    application.register(
        external
    )

    if application.count() != 2:
        raise RuntimeError(
            "Expected two runtimes."
        )

    if application.get(
        "runtime-application-002"
    ) is not external:
        raise RuntimeError(
            "External runtime was not registered."
        )

    print("REGISTER EXISTING: PASS")

    # -------------------------------------------------
    # ALL / IDS
    # -------------------------------------------------

    ids = application.ids()

    if set(ids) != {
        "runtime-application-001",
        "runtime-application-002",
    }:
        raise RuntimeError(
            "Runtime IDs are incorrect."
        )

    runtimes = application.all()

    if len(runtimes) != 2:
        raise RuntimeError(
            "all() should return two runtimes."
        )

    print("ALL / IDS: PASS")

    # -------------------------------------------------
    # STOP
    # -------------------------------------------------

    stopped = application.stop(
        "runtime-application-001"
    )

    if not stopped:
        raise RuntimeError(
            "Runtime should stop."
        )

    if runtime.active:
        raise RuntimeError(
            "Runtime should be inactive."
        )

    if not external.active:
        raise RuntimeError(
            "External runtime should remain active."
        )

    print("STOP: PASS")

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    removed = application.unregister(
        "runtime-application-001"
    )

    if not removed:
        raise RuntimeError(
            "Runtime should be unregistered."
        )

    if application.contains(
        "runtime-application-001"
    ):
        raise RuntimeError(
            "Unregistered runtime must not remain."
        )

    if application.count() != 1:
        raise RuntimeError(
            "One runtime should remain."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNREGISTER WITHOUT STOP
    # -------------------------------------------------

    removed = application.unregister(
        "runtime-application-002",
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

    application.create(
        "runtime-application-003"
    )

    application.create(
        "runtime-application-004"
    )

    if application.count() != 2:
        raise RuntimeError(
            "Expected two runtimes before clear."
        )

    cleared = application.clear()

    if cleared != 2:
        raise RuntimeError(
            "Expected two runtimes to be cleared."
        )

    if application.count() != 0:
        raise RuntimeError(
            "Application should be empty after clear."
        )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT RUNTIME APPLICATION: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()