from core.execution_context_application import (
    ExecutionContextApplication,
)
from core.execution_context_application_factory import (
    ExecutionContextApplicationFactory,
)


def main() -> None:
    # -------------------------------------------------
    # FACTORY CREATE
    # -------------------------------------------------

    application = (
        ExecutionContextApplicationFactory.create()
    )

    if not isinstance(
        application,
        ExecutionContextApplication,
    ):
        raise RuntimeError(
            "Factory must return ExecutionContextApplication."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if application.count() != 0:
        raise RuntimeError(
            "Factory-created application must start empty."
        )

    if application.all():
        raise RuntimeError(
            "Factory-created application must have no contexts."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE CONTEXT
    # -------------------------------------------------

    context = application.create(
        execution_id="factory-application-001",
        task_id="factory-application-task-001",
        session_id="factory-session-001",
        agent_id="factory-agent-001",
        workspace_root="D:\\AI_COMMAND_CENTER",
        working_directory="D:\\AI_COMMAND_CENTER\\workspace",
        permissions={
            "execution.read",
            "execution.write",
        },
        metadata={
            "source": "factory-application-test",
        },
    )

    if context.execution_id != (
        "factory-application-001"
    ):
        raise RuntimeError(
            "Execution ID is incorrect."
        )

    if context.task_id != (
        "factory-application-task-001"
    ):
        raise RuntimeError(
            "Task ID is incorrect."
        )

    if not context.has_permission(
        "execution.read"
    ):
        raise RuntimeError(
            "Permission was not preserved."
        )

    if application.count() != 1:
        raise RuntimeError(
            "Expected one active context."
        )

    print("CREATE CONTEXT: PASS")

    # -------------------------------------------------
    # LOOKUP
    # -------------------------------------------------

    found = application.get(
        context.context_id
    )

    if found is not context:
        raise RuntimeError(
            "Context lookup failed."
        )

    found_by_execution = (
        application.get_by_execution(
            "factory-application-001"
        )
    )

    if found_by_execution is not context:
        raise RuntimeError(
            "Execution lookup failed."
        )

    if not application.contains(
        context.context_id
    ):
        raise RuntimeError(
            "Context should exist."
        )

    print("LOOKUP: PASS")

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------

    updated = application.update_metadata(
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

    updated_agent = application.update_agent(
        context.context_id,
        "factory-agent-002",
    )

    if updated_agent.agent_id != (
        "factory-agent-002"
    ):
        raise RuntimeError(
            "Agent update failed."
        )

    print("UPDATES: PASS")

    # -------------------------------------------------
    # ISOLATION
    # -------------------------------------------------

    second_application = (
        ExecutionContextApplicationFactory.create()
    )

    if second_application.count() != 0:
        raise RuntimeError(
            "Factory instances must be isolated."
        )

    if second_application.get(
        context.context_id
    ) is not None:
        raise RuntimeError(
            "Context leaked into second instance."
        )

    if second_application.get_by_execution(
        "factory-application-001"
    ) is not None:
        raise RuntimeError(
            "Execution context leaked into second instance."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # SECOND INSTANCE OPERATION
    # -------------------------------------------------

    second_context = second_application.create(
        execution_id="factory-application-002",
        task_id="factory-application-task-002",
    )

    if second_application.count() != 1:
        raise RuntimeError(
            "Second application should contain one context."
        )

    if application.count() != 1:
        raise RuntimeError(
            "First application must remain isolated."
        )

    if second_context.execution_id != (
        "factory-application-002"
    ):
        raise RuntimeError(
            "Second context has incorrect execution ID."
        )

    print("SECOND INSTANCE: PASS")

    # -------------------------------------------------
    # REMOVE FIRST
    # -------------------------------------------------

    removed = application.remove_by_execution(
        "factory-application-001"
    )

    if not removed:
        raise RuntimeError(
            "First context should be removed."
        )

    if application.count() != 0:
        raise RuntimeError(
            "First application should be empty."
        )

    if second_application.count() != 1:
        raise RuntimeError(
            "Second application must remain unchanged."
        )

    print("REMOVE: PASS")

    # -------------------------------------------------
    # CLEAR SECOND
    # -------------------------------------------------

    cleared = second_application.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one context to be cleared."
        )

    if second_application.count() != 0:
        raise RuntimeError(
            "Second application should be empty."
        )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT APPLICATION FACTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()