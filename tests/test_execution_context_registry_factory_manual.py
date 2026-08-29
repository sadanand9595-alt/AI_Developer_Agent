from core.execution_context import ExecutionContext
from core.execution_context_registry import (
    ExecutionContextRegistry,
)
from core.execution_context_registry_factory import (
    ExecutionContextRegistryFactory,
)
from core.execution_context_registry_service import (
    ExecutionContextRegistryService,
)


def main() -> None:
    # -------------------------------------------------
    # FACTORY CREATE
    # -------------------------------------------------

    service = ExecutionContextRegistryFactory.create()

    if not isinstance(
        service,
        ExecutionContextRegistryService,
    ):
        raise RuntimeError(
            "Factory must return ExecutionContextRegistryService."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if service.count() != 0:
        raise RuntimeError(
            "Factory-created service must start empty."
        )

    if service.ids():
        raise RuntimeError(
            "Factory-created service must have no context IDs."
        )

    if service.all():
        raise RuntimeError(
            "Factory-created service must have no contexts."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE CONTEXT
    # -------------------------------------------------

    context = ExecutionContext.create(
        execution_id="factory-registry-execution-001",
        task_id="factory-registry-task-001",
        agent_id="agent-001",
    )

    service.register(context)

    if service.count() != 1:
        raise RuntimeError(
            "Expected one registered context."
        )

    if service.get(context.context_id) is not context:
        raise RuntimeError(
            "Factory-created service returned incorrect context."
        )

    print("CREATE CONTEXT: PASS")

    # -------------------------------------------------
    # LOOKUP
    # -------------------------------------------------

    found = service.get_by_execution(
        "factory-registry-execution-001"
    )

    if found is not context:
        raise RuntimeError(
            "Execution lookup returned incorrect context."
        )

    if not service.contains(
        context.context_id
    ):
        raise RuntimeError(
            "Context should be registered."
        )

    print("LOOKUP: PASS")

    # -------------------------------------------------
    # FACTORY ISOLATION
    # -------------------------------------------------

    second_service = (
        ExecutionContextRegistryFactory.create()
    )

    if second_service.count() != 0:
        raise RuntimeError(
            "Factory instances must be isolated."
        )

    if second_service.get(
        context.context_id
    ) is not None:
        raise RuntimeError(
            "Context leaked into second factory instance."
        )

    if second_service.contains(
        context.context_id
    ):
        raise RuntimeError(
            "Context must not exist in second instance."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # SECOND INSTANCE
    # -------------------------------------------------

    second_context = ExecutionContext.create(
        execution_id="factory-registry-execution-002",
        task_id="factory-registry-task-002",
        agent_id="agent-002",
    )

    second_service.register(
        second_context
    )

    if second_service.count() != 1:
        raise RuntimeError(
            "Second service should contain one context."
        )

    if service.count() != 1:
        raise RuntimeError(
            "First service must remain isolated."
        )

    if second_service.get(
        second_context.context_id
    ) is not second_context:
        raise RuntimeError(
            "Second service returned incorrect context."
        )

    print("SECOND INSTANCE: PASS")

    # -------------------------------------------------
    # REMOVE
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

    if service.count() != 0:
        raise RuntimeError(
            "First service should be empty."
        )

    if second_service.count() != 1:
        raise RuntimeError(
            "Second service must remain unchanged."
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
    print("EXECUTION CONTEXT REGISTRY FACTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
