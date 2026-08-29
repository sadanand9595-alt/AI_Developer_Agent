from core.execution_context import ExecutionContext
from core.execution_context_coordinator import (
    ExecutionContextCoordinator,
)
from core.execution_context_coordinator_factory import (
    ExecutionContextCoordinatorFactory,
)


def main() -> None:
    # -------------------------------------------------
    # FACTORY CREATE
    # -------------------------------------------------

    coordinator = (
        ExecutionContextCoordinatorFactory.create()
    )

    if not isinstance(
        coordinator,
        ExecutionContextCoordinator,
    ):
        raise RuntimeError(
            "Factory must return ExecutionContextCoordinator."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if coordinator.count() != 0:
        raise RuntimeError(
            "Factory-created coordinator must start empty."
        )

    if coordinator.all():
        raise RuntimeError(
            "Factory-created coordinator must have no contexts."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    context = coordinator.create(
        execution_id="factory-coordinator-001",
        task_id="factory-task-001",
        session_id="factory-session-001",
        agent_id="factory-agent-001",
        workspace_root="D:\\AI_COMMAND_CENTER",
        working_directory="D:\\AI_COMMAND_CENTER\\workspace",
        permissions={
            "execution.read",
            "execution.write",
        },
        metadata={
            "source": "factory-test",
        },
    )

    if not isinstance(
        context,
        ExecutionContext,
    ):
        raise RuntimeError(
            "create() must return ExecutionContext."
        )

    if coordinator.count() != 1:
        raise RuntimeError(
            "Expected one active context."
        )

    print("CREATE: PASS")

    # -------------------------------------------------
    # LOOKUP
    # -------------------------------------------------

    found = coordinator.get(
        context.context_id
    )

    if found is not context:
        raise RuntimeError(
            "Context lookup failed."
        )

    found_by_execution = (
        coordinator.get_by_execution(
            "factory-coordinator-001"
        )
    )

    if found_by_execution is not context:
        raise RuntimeError(
            "Execution lookup failed."
        )

    print("LOOKUP: PASS")

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------

    updated = coordinator.update_metadata(
        context.context_id,
        environment="test",
        factory=True,
    )

    if updated.metadata.get(
        "environment"
    ) != "test":
        raise RuntimeError(
            "Metadata update failed."
        )

    if updated.metadata.get(
        "factory"
    ) is not True:
        raise RuntimeError(
            "Factory metadata update failed."
        )

    print("UPDATE: PASS")

    # -------------------------------------------------
    # ISOLATION
    # -------------------------------------------------

    second = (
        ExecutionContextCoordinatorFactory.create()
    )

    if second.count() != 0:
        raise RuntimeError(
            "Factory instances must be isolated."
        )

    if second.get(
        context.context_id
    ) is not None:
        raise RuntimeError(
            "Context leaked into second factory instance."
        )

    if second.get_by_execution(
        "factory-coordinator-001"
    ) is not None:
        raise RuntimeError(
            "Execution context leaked into second instance."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # SECOND INSTANCE OPERATION
    # -------------------------------------------------

    second_context = second.create(
        execution_id="factory-coordinator-002",
        task_id="factory-task-002",
    )

    if second.count() != 1:
        raise RuntimeError(
            "Second coordinator should contain one context."
        )

    if coordinator.count() != 1:
        raise RuntimeError(
            "First coordinator must remain isolated."
        )

    if second_context.execution_id != (
        "factory-coordinator-002"
    ):
        raise RuntimeError(
            "Second context has incorrect execution ID."
        )

    print("SECOND INSTANCE: PASS")

    # -------------------------------------------------
    # REMOVE FIRST
    # -------------------------------------------------

    removed = coordinator.remove_by_execution(
        "factory-coordinator-001"
    )

    if not removed:
        raise RuntimeError(
            "First context should be removed."
        )

    if coordinator.count() != 0:
        raise RuntimeError(
            "First coordinator should be empty."
        )

    if second.count() != 1:
        raise RuntimeError(
            "Second coordinator must remain unchanged."
        )

    print("REMOVE: PASS")

    # -------------------------------------------------
    # CLEAR SECOND
    # -------------------------------------------------

    cleared = second.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one context to be cleared."
        )

    if second.count() != 0:
        raise RuntimeError(
            "Second coordinator should be empty."
        )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT COORDINATOR FACTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()