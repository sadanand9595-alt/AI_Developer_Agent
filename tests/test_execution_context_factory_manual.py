from core.execution_context_factory import (
    ExecutionContextFactory,
)
from core.execution_context_service import (
    ExecutionContextService,
)


def main() -> None:
    # -------------------------------------------------
    # FACTORY CREATE
    # -------------------------------------------------

    service = ExecutionContextFactory.create()

    if not isinstance(
        service,
        ExecutionContextService,
    ):
        raise RuntimeError(
            "Factory must return ExecutionContextService."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if service.count() != 0:
        raise RuntimeError(
            "Factory-created service must start empty."
        )

    if service.all():
        raise RuntimeError(
            "Factory-created service must have no contexts."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE CONTEXT
    # -------------------------------------------------

    context = service.create(
        execution_id="factory-context-001",
        task_id="factory-task-001",
        session_id="factory-session-001",
        agent_id="factory-agent-001",
        permissions={
            "execution.read",
            "execution.write",
        },
        metadata={
            "source": "factory-test",
        },
    )

    if context.execution_id != (
        "factory-context-001"
    ):
        raise RuntimeError(
            "Execution ID is incorrect."
        )

    if context.task_id != "factory-task-001":
        raise RuntimeError(
            "Task ID is incorrect."
        )

    if not context.has_permission(
        "execution.read"
    ):
        raise RuntimeError(
            "Permission was not preserved."
        )

    if service.count() != 1:
        raise RuntimeError(
            "Expected one context."
        )

    print("CREATE CONTEXT: PASS")

    # -------------------------------------------------
    # LOOKUP
    # -------------------------------------------------

    found = service.get(
        context.context_id
    )

    if found is not context:
        raise RuntimeError(
            "Context lookup failed."
        )

    by_execution = service.get_by_execution(
        "factory-context-001"
    )

    if by_execution is not context:
        raise RuntimeError(
            "Execution lookup failed."
        )

    print("LOOKUP: PASS")

    # -------------------------------------------------
    # SECOND FACTORY INSTANCE
    # -------------------------------------------------

    second_service = (
        ExecutionContextFactory.create()
    )

    if second_service.count() != 0:
        raise RuntimeError(
            "Factory instances must be isolated."
        )

    if second_service.get_by_execution(
        "factory-context-001"
    ) is not None:
        raise RuntimeError(
            "Context leaked between factory instances."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # SECOND CONTEXT
    # -------------------------------------------------

    second_context = second_service.create(
        execution_id="factory-context-002",
        task_id="factory-task-002",
    )

    if second_context.context_id == context.context_id:
        raise RuntimeError(
            "Context IDs must be unique."
        )

    if second_service.count() != 1:
        raise RuntimeError(
            "Second service should contain one context."
        )

    print("SECOND INSTANCE OPERATION: PASS")

    # -------------------------------------------------
    # REMOVE
    # -------------------------------------------------

    removed = service.remove_by_execution(
        "factory-context-001"
    )

    if not removed:
        raise RuntimeError(
            "Context should be removable."
        )

    if service.count() != 0:
        raise RuntimeError(
            "Context should be removed."
        )

    print("REMOVE: PASS")

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    cleared = second_service.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one context to be cleared."
        )

    if second_service.count() != 0:
        raise RuntimeError(
            "Second service should be empty."
        )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT FACTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()