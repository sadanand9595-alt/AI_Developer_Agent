from core.execution_context import ExecutionContext
from core.execution_context_application import (
    ExecutionContextApplication,
)


def main() -> None:
    application = ExecutionContextApplication()

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if application.count() != 0:
        raise RuntimeError(
            "Application must start empty."
        )

    if application.all():
        raise RuntimeError(
            "Application must initially have no contexts."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    context = application.create(
        execution_id="application-context-001",
        task_id="application-task-001",
        session_id="application-session-001",
        agent_id="application-agent-001",
        workspace_root="D:\\AI_COMMAND_CENTER",
        working_directory="D:\\AI_COMMAND_CENTER\\workspace",
        permissions={
            "execution.read",
            "execution.write",
        },
        metadata={
            "source": "application-test",
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

    if application.count() != 1:
        raise RuntimeError(
            "Expected one active context."
        )

    print("CREATE: PASS")

    # -------------------------------------------------
    # LOOKUP
    # -------------------------------------------------

    found = application.get(
        context.context_id
    )

    if found is not context:
        raise RuntimeError(
            "get() returned incorrect context."
        )

    found_by_execution = (
        application.get_by_execution(
            "application-context-001"
        )
    )

    if found_by_execution is not context:
        raise RuntimeError(
            "get_by_execution() returned incorrect context."
        )

    if not application.contains(
        context.context_id
    ):
        raise RuntimeError(
            "Created context should exist."
        )

    print("GET: PASS")
    print("GET BY EXECUTION: PASS")
    print("CONTAINS: PASS")

    # -------------------------------------------------
    # METADATA UPDATE
    # -------------------------------------------------

    updated = application.update_metadata(
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
            "Metadata environment update failed."
        )

    if updated.metadata.get(
        "attempt"
    ) != 1:
        raise RuntimeError(
            "Metadata attempt update failed."
        )

    if application.get(
        context.context_id
    ) is not updated:
        raise RuntimeError(
            "Updated context was not registered."
        )

    print("METADATA UPDATE: PASS")

    # -------------------------------------------------
    # WORKING DIRECTORY
    # -------------------------------------------------

    updated_directory = (
        application.update_working_directory(
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

    if application.get(
        context.context_id
    ) is not updated_directory:
        raise RuntimeError(
            "Updated directory context was not registered."
        )

    print("WORKING DIRECTORY UPDATE: PASS")

    # -------------------------------------------------
    # AGENT
    # -------------------------------------------------

    updated_agent = application.update_agent(
        context.context_id,
        "application-agent-002",
    )

    if updated_agent.agent_id != (
        "application-agent-002"
    ):
        raise RuntimeError(
            "Agent update failed."
        )

    if application.get(
        context.context_id
    ) is not updated_agent:
        raise RuntimeError(
            "Updated agent context was not registered."
        )

    print("AGENT UPDATE: PASS")

    # -------------------------------------------------
    # ORIGINAL IMMUTABILITY
    # -------------------------------------------------

    if context.agent_id != (
        "application-agent-001"
    ):
        raise RuntimeError(
            "Original context was modified."
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
            "Original metadata was modified."
        )

    print("IMMUTABILITY: PASS")

    # -------------------------------------------------
    # REGISTER EXISTING
    # -------------------------------------------------

    external = ExecutionContext.create(
        execution_id="application-context-002",
        task_id="application-task-002",
    )

    application.register(
        external
    )

    if application.count() != 2:
        raise RuntimeError(
            "Expected two active contexts."
        )

    if application.get(
        external.context_id
    ) is not external:
        raise RuntimeError(
            "External context was not registered."
        )

    print("REGISTER EXISTING: PASS")

    # -------------------------------------------------
    # ALL
    # -------------------------------------------------

    contexts = application.all()

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

    removed = application.remove_by_execution(
        "application-context-002"
    )

    if not removed:
        raise RuntimeError(
            "Context should be removed by execution ID."
        )

    if application.get_by_execution(
        "application-context-002"
    ) is not None:
        raise RuntimeError(
            "Removed context should not remain."
        )

    if application.count() != 1:
        raise RuntimeError(
            "Expected one remaining context."
        )

    print("REMOVE BY EXECUTION: PASS")

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    current = application.get(
        context.context_id
    )

    if current is None:
        raise RuntimeError(
            "Current context should exist."
        )

    removed = application.unregister(
        current.context_id
    )

    if not removed:
        raise RuntimeError(
            "Context should be unregistered."
        )

    if application.count() != 0:
        raise RuntimeError(
            "Application should be empty."
        )

    if application.contains(
        current.context_id
    ):
        raise RuntimeError(
            "Unregistered context must not remain."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNKNOWN OPERATIONS
    # -------------------------------------------------

    if application.unregister(
        "missing-context"
    ):
        raise RuntimeError(
            "Unknown context should not unregister."
        )

    if application.remove_by_execution(
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
        application.update_metadata(
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

    application.create(
        execution_id="application-context-003"
    )

    application.create(
        execution_id="application-context-004"
    )

    if application.count() != 2:
        raise RuntimeError(
            "Expected two contexts before clear."
        )

    cleared = application.clear()

    if cleared != 2:
        raise RuntimeError(
            "Expected two contexts to be cleared."
        )

    if application.count() != 0:
        raise RuntimeError(
            "Application should be empty after clear."
        )

    if application.all():
        raise RuntimeError(
            "No contexts should remain after clear."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    for bad_coordinator in ("not-a-coordinator", 123):
        try:
            ExecutionContextApplication(
                coordinator=bad_coordinator
            )
        except TypeError:
            pass
        else:
            raise RuntimeError(
                f"Invalid coordinator {bad_coordinator!r} should "
                "be rejected."
            )

    print("INVALID COORDINATOR DEPENDENCY: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT APPLICATION: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()