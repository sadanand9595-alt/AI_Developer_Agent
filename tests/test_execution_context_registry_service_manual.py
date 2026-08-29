from core.execution_context import ExecutionContext
from core.execution_context_registry import (
    ExecutionContextRegistry,
)
from core.execution_context_registry_service import (
    ExecutionContextRegistryService,
)


def main() -> None:
    registry = ExecutionContextRegistry()

    service = ExecutionContextRegistryService(
        registry
    )

    # -------------------------------------------------
    # SERVICE CREATION
    # -------------------------------------------------

    if not isinstance(
        service,
        ExecutionContextRegistryService,
    ):
        raise RuntimeError(
            "Service creation failed."
        )

    if service.count() != 0:
        raise RuntimeError(
            "Service should start empty."
        )

    print("SERVICE CREATE: PASS")
    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE CONTEXTS
    # -------------------------------------------------

    context_one = ExecutionContext.create(
        execution_id="registry-service-execution-001",
        task_id="registry-service-task-001",
        agent_id="agent-001",
    )

    context_two = ExecutionContext.create(
        execution_id="registry-service-execution-002",
        task_id="registry-service-task-002",
        agent_id="agent-002",
    )

    # -------------------------------------------------
    # REGISTER
    # -------------------------------------------------

    service.register(
        context_one
    )

    service.register(
        context_two
    )

    if service.count() != 2:
        raise RuntimeError(
            "Expected two registered contexts."
        )

    print("REGISTER: PASS")

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    found = service.get(
        context_one.context_id
    )

    if found is not context_one:
        raise RuntimeError(
            "get() returned incorrect context."
        )

    print("GET: PASS")

    # -------------------------------------------------
    # GET BY EXECUTION
    # -------------------------------------------------

    found_by_execution = (
        service.get_by_execution(
            "registry-service-execution-002"
        )
    )

    if found_by_execution is not context_two:
        raise RuntimeError(
            "get_by_execution() returned incorrect context."
        )

    print("GET BY EXECUTION: PASS")

    # -------------------------------------------------
    # CONTAINS
    # -------------------------------------------------

    if not service.contains(
        context_one.context_id
    ):
        raise RuntimeError(
            "Context one should exist."
        )

    if not service.contains(
        context_two.context_id
    ):
        raise RuntimeError(
            "Context two should exist."
        )

    if service.contains(
        "missing-context"
    ):
        raise RuntimeError(
            "Unknown context should not exist."
        )

    print("CONTAINS: PASS")

    # -------------------------------------------------
    # IDS
    # -------------------------------------------------

    ids = service.ids()

    if set(ids) != {
        context_one.context_id,
        context_two.context_id,
    }:
        raise RuntimeError(
            "Context IDs are incorrect."
        )

    print("IDS: PASS")

    # -------------------------------------------------
    # ALL
    # -------------------------------------------------

    contexts = service.all()

    if len(contexts) != 2:
        raise RuntimeError(
            "all() should return two contexts."
        )

    if context_one not in contexts:
        raise RuntimeError(
            "Context one missing from all()."
        )

    if context_two not in contexts:
        raise RuntimeError(
            "Context two missing from all()."
        )

    print("ALL: PASS")

    # -------------------------------------------------
    # INVALID DEPENDENCY
    # -------------------------------------------------

    try:
        ExecutionContextRegistryService(
            "invalid-registry"
        )
    except TypeError:
        print("INVALID DEPENDENCY: PASS")
    else:
        raise RuntimeError(
            "Invalid registry must be rejected."
        )

    # -------------------------------------------------
    # INVALID CONTEXT
    # -------------------------------------------------

    try:
        service.register(
            "invalid-context"
        )
    except TypeError:
        print("INVALID CONTEXT: PASS")
    else:
        raise RuntimeError(
            "Invalid context must be rejected."
        )

    # -------------------------------------------------
    # DUPLICATE PROTECTION
    # -------------------------------------------------

    try:
        service.register(
            context_one
        )
    except ValueError:
        print("DUPLICATE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Duplicate context must be rejected."
        )

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    removed = service.unregister(
        context_one.context_id
    )

    if not removed:
        raise RuntimeError(
            "Context one should be removed."
        )

    if service.contains(
        context_one.context_id
    ):
        raise RuntimeError(
            "Removed context must not remain."
        )

    if service.count() != 1:
        raise RuntimeError(
            "One context should remain."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNKNOWN UNREGISTER
    # -------------------------------------------------

    removed = service.unregister(
        "missing-context"
    )

    if removed:
        raise RuntimeError(
            "Unknown context should not be removed."
        )

    print("UNKNOWN UNREGISTER: PASS")

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    cleared = service.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one context to be cleared."
        )

    if service.count() != 0:
        raise RuntimeError(
            "Service should be empty after clear."
        )

    if service.ids():
        raise RuntimeError(
            "IDs should be empty after clear."
        )

    if service.all():
        raise RuntimeError(
            "Contexts should be empty after clear."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT REGISTRY SERVICE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()