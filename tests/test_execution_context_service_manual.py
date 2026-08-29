from core.execution_context import ExecutionContext
from core.execution_context_service import (
    ExecutionContextService,
)


def main() -> None:
    service = ExecutionContextService()

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if service.count() != 0:
        raise RuntimeError(
            "Service must start empty."
        )

    if service.all():
        raise RuntimeError(
            "Initial context collection must be empty."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    context = service.create(
        execution_id="context-service-execution-001",
        task_id="context-service-task-001",
        session_id="session-001",
        agent_id="agent-001",
        workspace_root="D:\\AI_COMMAND_CENTER",
        working_directory="D:\\AI_COMMAND_CENTER\\workspace",
        permissions={
            "execution.read",
            "execution.write",
        },
        metadata={
            "source": "service-test",
        },
    )

    if not isinstance(
        context,
        ExecutionContext,
    ):
        raise RuntimeError(
            "create() must return ExecutionContext."
        )

    if service.count() != 1:
        raise RuntimeError(
            "Expected one registered context."
        )

    print("CREATE: PASS")

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    found = service.get(
        context.context_id
    )

    if found is not context:
        raise RuntimeError(
            "get() returned the wrong context."
        )

    print("GET: PASS")

    # -------------------------------------------------
    # GET BY EXECUTION
    # -------------------------------------------------

    found_by_execution = (
        service.get_by_execution(
            "context-service-execution-001"
        )
    )

    if found_by_execution is not context:
        raise RuntimeError(
            "get_by_execution() returned the wrong context."
        )

    print("GET BY EXECUTION: PASS")

    # -------------------------------------------------
    # CONTAINS
    # -------------------------------------------------

    if not service.contains(
        context.context_id
    ):
        raise RuntimeError(
            "Context should be registered."
        )

    if service.contains(
        "missing-context-id"
    ):
        raise RuntimeError(
            "Unknown context must not exist."
        )

    print("CONTAINS: PASS")

    # -------------------------------------------------
    # CREATE SECOND CONTEXT
    # -------------------------------------------------

    second = service.create(
        execution_id="context-service-execution-002",
        task_id="context-service-task-002",
    )

    if second.context_id == context.context_id:
        raise RuntimeError(
            "Context IDs must be unique."
        )

    if service.count() != 2:
        raise RuntimeError(
            "Expected two contexts."
        )

    print("SECOND CREATE: PASS")

    # -------------------------------------------------
    # ALL
    # -------------------------------------------------

    contexts = service.all()

    if len(contexts) != 2:
        raise RuntimeError(
            "all() should return two contexts."
        )

    if context not in contexts:
        raise RuntimeError(
            "First context missing from all()."
        )

    if second not in contexts:
        raise RuntimeError(
            "Second context missing from all()."
        )

    print("ALL: PASS")

    # -------------------------------------------------
    # REGISTER EXISTING CONTEXT
    # -------------------------------------------------

    external = ExecutionContext.create(
        execution_id="context-service-execution-003"
    )

    service.register(
        external
    )

    if service.count() != 3:
        raise RuntimeError(
            "Existing context was not registered."
        )

    if service.get(
        external.context_id
    ) is not external:
        raise RuntimeError(
            "Registered context cannot be retrieved."
        )

    print("REGISTER EXISTING: PASS")

    # -------------------------------------------------
    # TYPE VALIDATION
    # -------------------------------------------------

    try:
        service.register(
            "invalid-context"
        )
    except TypeError:
        print("TYPE VALIDATION: PASS")
    else:
        raise RuntimeError(
            "Invalid context type should be rejected."
        )

    # -------------------------------------------------
    # DUPLICATE PROTECTION
    # -------------------------------------------------

    try:
        service.register(
            context
        )
    except ValueError:
        print("DUPLICATE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Duplicate context should be rejected."
        )

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    removed = service.unregister(
        context.context_id
    )

    if not removed:
        raise RuntimeError(
            "Context should be removed."
        )

    if service.contains(
        context.context_id
    ):
        raise RuntimeError(
            "Removed context must not remain."
        )

    if service.count() != 2:
        raise RuntimeError(
            "Expected two remaining contexts."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNKNOWN UNREGISTER
    # -------------------------------------------------

    removed = service.unregister(
        "unknown-context"
    )

    if removed:
        raise RuntimeError(
            "Unknown context should not be removed."
        )

    print("UNKNOWN UNREGISTER: PASS")

    # -------------------------------------------------
    # REMOVE BY EXECUTION
    # -------------------------------------------------

    removed = service.remove_by_execution(
        "context-service-execution-002"
    )

    if not removed:
        raise RuntimeError(
            "Context should be removed by execution ID."
        )

    if service.get_by_execution(
        "context-service-execution-002"
    ) is not None:
        raise RuntimeError(
            "Context should no longer exist."
        )

    if service.count() != 1:
        raise RuntimeError(
            "Expected one remaining context."
        )

    print("REMOVE BY EXECUTION: PASS")

    # -------------------------------------------------
    # UNKNOWN EXECUTION REMOVAL
    # -------------------------------------------------

    removed = service.remove_by_execution(
        "unknown-execution"
    )

    if removed:
        raise RuntimeError(
            "Unknown execution should not remove anything."
        )

    print("UNKNOWN EXECUTION REMOVAL: PASS")

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

    if service.all():
        raise RuntimeError(
            "No contexts should remain after clear."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT SERVICE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()