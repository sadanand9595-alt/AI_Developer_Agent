from core.execution_context import ExecutionContext


def main() -> None:
    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    context = ExecutionContext.create(
        execution_id="execution-context-001",
        task_id="task-context-001",
        session_id="session-001",
        agent_id="agent-001",
        workspace_root="D:\\AI_COMMAND_CENTER",
        working_directory="D:\\AI_COMMAND_CENTER\\workspace",
        permissions={
            "execution.read",
            "execution.write",
        },
        metadata={
            "source": "manual-test",
            "priority": "high",
        },
    )

    if context.execution_id != (
        "execution-context-001"
    ):
        raise RuntimeError(
            "Execution ID is incorrect."
        )

    if context.task_id != "task-context-001":
        raise RuntimeError(
            "Task ID is incorrect."
        )

    if context.session_id != "session-001":
        raise RuntimeError(
            "Session ID is incorrect."
        )

    if context.agent_id != "agent-001":
        raise RuntimeError(
            "Agent ID is incorrect."
        )

    print("CREATE: PASS")

    # -------------------------------------------------
    # PERMISSIONS
    # -------------------------------------------------

    if not context.has_permission(
        "execution.read"
    ):
        raise RuntimeError(
            "execution.read permission should exist."
        )

    if context.has_permission(
        "execution.delete"
    ):
        raise RuntimeError(
            "execution.delete must not exist."
        )

    print("HAS PERMISSION: PASS")

    context.require_permission(
        "execution.read"
    )

    print("REQUIRE PERMISSION: PASS")

    try:
        context.require_permission(
            "execution.delete"
        )
    except PermissionError:
        print("MISSING PERMISSION: PASS")
    else:
        raise RuntimeError(
            "Missing permission should raise PermissionError."
        )

    # -------------------------------------------------
    # IMMUTABILITY
    # -------------------------------------------------

    try:
        context.execution_id = "modified"
    except (
        AttributeError,
        TypeError,
    ):
        print("IMMUTABILITY: PASS")
    else:
        raise RuntimeError(
            "ExecutionContext must be immutable."
        )

    # -------------------------------------------------
    # METADATA COPY
    # -------------------------------------------------

    updated = context.with_metadata(
        environment="test",
        attempt=1,
    )

    if context.metadata.get(
        "environment"
    ) is not None:
        raise RuntimeError(
            "Original context must remain unchanged."
        )

    if updated.metadata.get(
        "environment"
    ) != "test":
        raise RuntimeError(
            "Updated metadata was not stored."
        )

    if updated.metadata.get(
        "attempt"
    ) != 1:
        raise RuntimeError(
            "Updated attempt was not stored."
        )

    if updated.execution_id != (
        context.execution_id
    ):
        raise RuntimeError(
            "Execution ID must remain unchanged."
        )

    if updated.context_id != (
        context.context_id
    ):
        raise RuntimeError(
            "Context ID must remain stable."
        )

    print("WITH METADATA: PASS")

    # -------------------------------------------------
    # WORKING DIRECTORY
    # -------------------------------------------------

    changed_directory = (
        context.with_working_directory(
            "D:\\AI_COMMAND_CENTER\\workspace\\project"
        )
    )

    if changed_directory.working_directory != (
        "D:\\AI_COMMAND_CENTER\\workspace\\project"
    ):
        raise RuntimeError(
            "Working directory was not updated."
        )

    if context.working_directory == (
        changed_directory.working_directory
    ):
        raise RuntimeError(
            "Original context must not be modified."
        )

    if changed_directory.context_id != (
        context.context_id
    ):
        raise RuntimeError(
            "Context ID must remain stable."
        )

    print("WITH WORKING DIRECTORY: PASS")

    # -------------------------------------------------
    # AGENT
    # -------------------------------------------------

    changed_agent = context.with_agent(
        "agent-002"
    )

    if changed_agent.agent_id != "agent-002":
        raise RuntimeError(
            "Agent ID was not updated."
        )

    if context.agent_id != "agent-001":
        raise RuntimeError(
            "Original agent ID must remain unchanged."
        )

    if changed_agent.execution_id != (
        context.execution_id
    ):
        raise RuntimeError(
            "Execution ID must remain unchanged."
        )

    print("WITH AGENT: PASS")

    # -------------------------------------------------
    # UNIQUE CONTEXT ID
    # -------------------------------------------------

    second = ExecutionContext.create(
        execution_id="execution-context-002"
    )

    if second.context_id == context.context_id:
        raise RuntimeError(
            "Each new context must have a unique context ID."
        )

    print("UNIQUE CONTEXT ID: PASS")

    # -------------------------------------------------
    # EMPTY EXECUTION ID
    # -------------------------------------------------

    try:
        ExecutionContext.create(
            execution_id="   "
        )
    except ValueError:
        print("EMPTY EXECUTION ID: PASS")
    else:
        raise RuntimeError(
            "Empty execution ID should be rejected."
        )

    # -------------------------------------------------
    # DEFAULTS
    # -------------------------------------------------

    default_context = ExecutionContext.create(
        execution_id="execution-default-001"
    )

    if default_context.workspace_root != ".":
        raise RuntimeError(
            "Default workspace root should be '.'."
        )

    if default_context.working_directory != ".":
        raise RuntimeError(
            "Default working directory should be '.'."
        )

    if default_context.permissions != frozenset():
        raise RuntimeError(
            "Default permissions should be empty."
        )

    if default_context.metadata != {}:
        raise RuntimeError(
            "Default metadata should be empty."
        )

    print("DEFAULTS: PASS")

    # -------------------------------------------------
    # NON-STRING EXECUTION ID (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------

    for bad_id in (None, 123, ["not", "a", "string"]):
        try:
            ExecutionContext.create(
                execution_id=bad_id
            )
        except ValueError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "create() raised unexpected exception for "
                f"execution_id={bad_id!r}: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"Non-string execution_id {bad_id!r} should "
                "be rejected."
            )

    print("NON-STRING EXECUTION ID: PASS")

    # -------------------------------------------------
    # INVALID PERMISSIONS TYPE
    # -------------------------------------------------

    for bad_permissions in (123, "not-a-set", ["a", "b"]):
        try:
            ExecutionContext.create(
                execution_id="execution-invalid-permissions",
                permissions=bad_permissions,
            )
        except ValueError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "create() raised unexpected exception for "
                f"permissions={bad_permissions!r}: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"Invalid permissions {bad_permissions!r} should "
                "be rejected."
            )

    print("INVALID PERMISSIONS TYPE: PASS")

    # -------------------------------------------------
    # INVALID METADATA TYPE
    # -------------------------------------------------
    #
    # A non-dict metadata must be rejected at create()
    # rather than silently accepted and later crashing
    # with_metadata()'s dict.update() call.
    # -------------------------------------------------

    for bad_metadata in (123, "not-a-dict", ["a", "b"]):
        try:
            ExecutionContext.create(
                execution_id="execution-invalid-metadata",
                metadata=bad_metadata,
            )
        except ValueError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "create() raised unexpected exception for "
                f"metadata={bad_metadata!r}: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"Invalid metadata {bad_metadata!r} should "
                "be rejected."
            )

    print("INVALID METADATA TYPE: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()