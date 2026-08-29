from core.execution_context_runtime import (
    ExecutionContextRuntime,
)
from core.execution_context_runtime_service import (
    ExecutionContextRuntimeService,
)


def main() -> None:
    service = ExecutionContextRuntimeService()

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if service.count() != 0:
        raise RuntimeError(
            "Service must start empty."
        )

    if service.ids():
        raise RuntimeError(
            "Runtime IDs must initially be empty."
        )

    if service.all():
        raise RuntimeError(
            "Runtime collection must initially be empty."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    runtime = service.create(
        "runtime-service-001"
    )

    if not isinstance(
        runtime,
        ExecutionContextRuntime,
    ):
        raise RuntimeError(
            "create() must return ExecutionContextRuntime."
        )

    if runtime.context_id != (
        "runtime-service-001"
    ):
        raise RuntimeError(
            "Runtime context ID is incorrect."
        )

    if service.count() != 1:
        raise RuntimeError(
            "Expected one runtime."
        )

    print("CREATE: PASS")

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    found = service.get(
        "runtime-service-001"
    )

    if found is not runtime:
        raise RuntimeError(
            "get() returned the wrong runtime."
        )

    if service.get(
        "missing-runtime"
    ) is not None:
        raise RuntimeError(
            "Unknown runtime should return None."
        )

    print("GET: PASS")

    # -------------------------------------------------
    # CONTAINS
    # -------------------------------------------------

    if not service.contains(
        "runtime-service-001"
    ):
        raise RuntimeError(
            "Runtime should exist."
        )

    if service.contains(
        "missing-runtime"
    ):
        raise RuntimeError(
            "Unknown runtime must not exist."
        )

    print("CONTAINS: PASS")

    # -------------------------------------------------
    # RUNTIME OPERATION
    # -------------------------------------------------

    runtime.start_step(
        "execute"
    )

    runtime.complete_step()

    if runtime.completed_steps != 1:
        raise RuntimeError(
            "Runtime operation failed."
        )

    print("RUNTIME OPERATION: PASS")

    # -------------------------------------------------
    # DUPLICATE CREATE
    # -------------------------------------------------

    try:
        service.create(
            "runtime-service-001"
        )
    except ValueError:
        print("DUPLICATE CREATE: PASS")
    else:
        raise RuntimeError(
            "Duplicate runtime should be rejected."
        )

    # -------------------------------------------------
    # INVALID CONTEXT ID
    # -------------------------------------------------

    try:
        service.create(
            "   "
        )
    except ValueError:
        print("INVALID CONTEXT ID: PASS")
    else:
        raise RuntimeError(
            "Empty context ID should be rejected."
        )

    # -------------------------------------------------
    # REGISTER EXISTING
    # -------------------------------------------------

    external = ExecutionContextRuntime(
        context_id="runtime-service-002"
    )

    service.register(
        external
    )

    if service.count() != 2:
        raise RuntimeError(
            "Expected two runtimes."
        )

    if service.get(
        "runtime-service-002"
    ) is not external:
        raise RuntimeError(
            "External runtime was not registered."
        )

    print("REGISTER EXISTING: PASS")

    # -------------------------------------------------
    # TYPE VALIDATION
    # -------------------------------------------------

    try:
        service.register(
            "invalid-runtime"
        )
    except TypeError:
        print("TYPE VALIDATION: PASS")
    else:
        raise RuntimeError(
            "Invalid runtime type should be rejected."
        )

    # -------------------------------------------------
    # DUPLICATE REGISTER
    # -------------------------------------------------

    try:
        service.register(
            runtime
        )
    except ValueError:
        print("DUPLICATE REGISTER: PASS")
    else:
        raise RuntimeError(
            "Duplicate runtime should be rejected."
        )

    # -------------------------------------------------
    # IDS
    # -------------------------------------------------

    ids = service.ids()

    if set(ids) != {
        "runtime-service-001",
        "runtime-service-002",
    }:
        raise RuntimeError(
            "Runtime IDs are incorrect."
        )

    print("IDS: PASS")

    # -------------------------------------------------
    # ALL
    # -------------------------------------------------

    runtimes = service.all()

    if len(runtimes) != 2:
        raise RuntimeError(
            "all() should return two runtimes."
        )

    if runtime not in runtimes:
        raise RuntimeError(
            "First runtime missing."
        )

    if external not in runtimes:
        raise RuntimeError(
            "External runtime missing."
        )

    print("ALL: PASS")

    # -------------------------------------------------
    # STOP
    # -------------------------------------------------

    stopped = service.stop(
        "runtime-service-001"
    )

    if not stopped:
        raise RuntimeError(
            "Runtime should be stopped."
        )

    if runtime.active:
        raise RuntimeError(
            "Runtime should be inactive."
        )

    print("STOP: PASS")

    # -------------------------------------------------
    # UNKNOWN STOP
    # -------------------------------------------------

    stopped = service.stop(
        "missing-runtime"
    )

    if stopped:
        raise RuntimeError(
            "Unknown runtime should not be stopped."
        )

    print("UNKNOWN STOP: PASS")

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    removed = service.unregister(
        "runtime-service-001"
    )

    if not removed:
        raise RuntimeError(
            "Runtime should be unregistered."
        )

    if service.contains(
        "runtime-service-001"
    ):
        raise RuntimeError(
            "Unregistered runtime must not remain."
        )

    if service.count() != 1:
        raise RuntimeError(
            "One runtime should remain."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNREGISTER WITHOUT STOP
    # -------------------------------------------------

    active_runtime = service.get(
        "runtime-service-002"
    )

    if active_runtime is None:
        raise RuntimeError(
            "Second runtime should exist."
        )

    removed = service.unregister(
        "runtime-service-002",
        stop=False,
    )

    if not removed:
        raise RuntimeError(
            "Runtime should be unregistered."
        )

    if not active_runtime.active:
        raise RuntimeError(
            "stop=False must not stop runtime."
        )

    if service.count() != 0:
        raise RuntimeError(
            "Service should be empty."
        )

    print("UNREGISTER WITHOUT STOP: PASS")

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    service.create(
        "runtime-service-003"
    )

    service.create(
        "runtime-service-004"
    )

    runtime_three = service.get(
        "runtime-service-003"
    )

    runtime_four = service.get(
        "runtime-service-004"
    )

    if runtime_three is None or runtime_four is None:
        raise RuntimeError(
            "Runtimes should exist before clear."
        )

    cleared = service.clear()

    if cleared != 2:
        raise RuntimeError(
            "Expected two runtimes to be cleared."
        )

    if service.count() != 0:
        raise RuntimeError(
            "Service should be empty after clear."
        )

    if runtime_three.active:
        raise RuntimeError(
            "Clear should stop runtime three."
        )

    if runtime_four.active:
        raise RuntimeError(
            "Clear should stop runtime four."
        )

    print("CLEAR: PASS")

    # -------------------------------------------------
    # FINAL
    # -------------------------------------------------

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT RUNTIME SERVICE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()