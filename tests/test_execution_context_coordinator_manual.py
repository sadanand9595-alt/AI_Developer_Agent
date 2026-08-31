from core.execution_context import ExecutionContext
from core.execution_context_coordinator import (
    ExecutionContextCoordinator,
)


def main() -> None:
    coordinator = ExecutionContextCoordinator()

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if coordinator.count() != 0:
        raise RuntimeError(
            "Coordinator must start empty."
        )

    if coordinator.all():
        raise RuntimeError(
            "Coordinator must initially have no contexts."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    context = coordinator.create(
        execution_id="coordinator-context-001",
        task_id="coordinator-task-001",
        session_id="session-001",
        agent_id="agent-001",
        workspace_root="D:\\AI_COMMAND_CENTER",
        working_directory="D:\\AI_COMMAND_CENTER\\workspace",
        permissions={
            "execution.read",
            "execution.write",
        },
        metadata={
            "source": "coordinator-test",
            "priority": "high",
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

    if not coordinator.contains(
        context.context_id
    ):
        raise RuntimeError(
            "Created context should be registered."
        )

    print("CREATE: PASS")
    print("REGISTRATION: PASS")

    # -------------------------------------------------
    # LOOKUP
    # -------------------------------------------------

    found = coordinator.get(
        context.context_id
    )

    if found is not context:
        raise RuntimeError(
            "get() returned incorrect context."
        )

    found_by_execution = (
        coordinator.get_by_execution(
            "coordinator-context-001"
        )
    )

    if found_by_execution is not context:
        raise RuntimeError(
            "get_by_execution() returned incorrect context."
        )

    print("GET: PASS")
    print("GET BY EXECUTION: PASS")

    # -------------------------------------------------
    # METADATA UPDATE
    # -------------------------------------------------

    updated = coordinator.update_metadata(
        context.context_id,
        environment="test",
        attempt=1,
    )

    if updated.context_id != context.context_id:
        raise RuntimeError(
            "Context ID must remain stable."
        )

    if updated.metadata.get(
        "environment"
    ) != "test":
        raise RuntimeError(
            "Metadata update failed."
        )

    if updated.metadata.get(
        "attempt"
    ) != 1:
        raise RuntimeError(
            "Metadata attempt update failed."
        )

    if coordinator.get(
        context.context_id
    ) is not updated:
        raise RuntimeError(
            "Updated context was not registered."
        )

    print("METADATA UPDATE: PASS")

    # -------------------------------------------------
    # WORKING DIRECTORY UPDATE
    # -------------------------------------------------

    updated_directory = (
        coordinator.update_working_directory(
            context.context_id,
            "D:\\AI_COMMAND_CENTER\\workspace\\project",
        )
    )

    if updated_directory.working_directory != (
        "D:\\AI_COMMAND_CENTER\\workspace\\project"
    ):
        raise RuntimeError(
            "Working directory update failed."
        )

    if coordinator.get(
        context.context_id
    ) is not updated_directory:
        raise RuntimeError(
            "Updated directory context was not registered."
        )

    print("WORKING DIRECTORY UPDATE: PASS")

    # -------------------------------------------------
    # AGENT UPDATE
    # -------------------------------------------------

    updated_agent = coordinator.update_agent(
        context.context_id,
        "agent-002",
    )

    if updated_agent.agent_id != "agent-002":
        raise RuntimeError(
            "Agent update failed."
        )

    if coordinator.get(
        context.context_id
    ) is not updated_agent:
        raise RuntimeError(
            "Updated agent context was not registered."
        )

    print("AGENT UPDATE: PASS")

    # -------------------------------------------------
    # IMMUTABLE ORIGINAL
    # -------------------------------------------------

    if context.agent_id != "agent-001":
        raise RuntimeError(
            "Original context was unexpectedly modified."
        )

    if context.working_directory != (
        "D:\\AI_COMMAND_CENTER\\workspace"
    ):
        raise RuntimeError(
            "Original working directory was modified."
        )

    if context.metadata.get(
        "environment"
    ) is not None:
        raise RuntimeError(
            "Original metadata was unexpectedly modified."
        )

    print("IMMUTABILITY: PASS")

    # -------------------------------------------------
    # REGISTER EXISTING
    # -------------------------------------------------

    external = ExecutionContext.create(
        execution_id="coordinator-context-002",
        task_id="coordinator-task-002",
    )

    coordinator.register(
        external
    )

    if coordinator.count() != 2:
        raise RuntimeError(
            "Expected two active contexts."
        )

    if coordinator.get(
        external.context_id
    ) is not external:
        raise RuntimeError(
            "External context was not registered."
        )

    print("REGISTER EXISTING: PASS")

    # -------------------------------------------------
    # ALL
    # -------------------------------------------------

    contexts = coordinator.all()

    if len(contexts) != 2:
        raise RuntimeError(
            "all() should return two contexts."
        )

    if updated_agent not in contexts:
        raise RuntimeError(
            "Updated context missing from all()."
        )

    if external not in contexts:
        raise RuntimeError(
            "External context missing from all()."
        )

    print("ALL: PASS")

    # -------------------------------------------------
    # REMOVE BY EXECUTION
    # -------------------------------------------------

    removed = coordinator.remove_by_execution(
        "coordinator-context-002"
    )

    if not removed:
        raise RuntimeError(
            "Context should be removed by execution ID."
        )

    if coordinator.get_by_execution(
        "coordinator-context-002"
    ) is not None:
        raise RuntimeError(
            "Removed context should not be queryable."
        )

    if coordinator.count() != 1:
        raise RuntimeError(
            "Expected one remaining context."
        )

    print("REMOVE BY EXECUTION: PASS")

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    current = coordinator.get(
        context.context_id
    )

    if current is None:
        raise RuntimeError(
            "Current context should exist."
        )

    removed = coordinator.unregister(
        current.context_id
    )

    if not removed:
        raise RuntimeError(
            "Context should be unregistered."
        )

    if coordinator.count() != 0:
        raise RuntimeError(
            "Coordinator should be empty."
        )

    if coordinator.contains(
        current.context_id
    ):
        raise RuntimeError(
            "Unregistered context must not remain."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNKNOWN OPERATIONS
    # -------------------------------------------------

    if coordinator.unregister(
        "missing-context"
    ):
        raise RuntimeError(
            "Unknown context should not unregister."
        )

    if coordinator.remove_by_execution(
        "missing-execution"
    ):
        raise RuntimeError(
            "Unknown execution should not remove anything."
        )

    print("UNKNOWN OPERATIONS: PASS")

    # -------------------------------------------------
    # MISSING UPDATE
    # -------------------------------------------------

    try:
        coordinator.update_metadata(
            "missing-context",
            test=True,
        )
    except KeyError:
        print("MISSING UPDATE: PASS")
    else:
        raise RuntimeError(
            "Missing context update should raise KeyError."
        )

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    coordinator.create(
        execution_id="coordinator-context-003"
    )

    coordinator.create(
        execution_id="coordinator-context-004"
    )

    if coordinator.count() != 2:
        raise RuntimeError(
            "Expected two contexts before clear."
        )

    cleared = coordinator.clear()

    if cleared != 2:
        raise RuntimeError(
            "Expected two contexts to be cleared."
        )

    if coordinator.count() != 0:
        raise RuntimeError(
            "Coordinator should be empty after clear."
        )

    if coordinator.all():
        raise RuntimeError(
            "No contexts should remain after clear."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    for kwarg in ("context_service", "registry_service"):
        for bad_dependency in ("not-valid", 123):
            try:
                ExecutionContextCoordinator(
                    **{kwarg: bad_dependency}
                )
            except TypeError:
                pass
            else:
                raise RuntimeError(
                    f"Invalid {kwarg} {bad_dependency!r} should "
                    "be rejected."
                )

    print("INVALID DEPENDENCIES: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT COORDINATOR: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()