from core.context import ExecutionContext


def main() -> None:
    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    context = ExecutionContext.create(
        user_id="context-user-001",
        task_id="context-task-001",
        permissions={
            "read",
            "write",
        },
        metadata={
            "source": "manual-test",
        },
    )

    if context.user_id != "context-user-001":
        raise RuntimeError(
            "User ID is incorrect."
        )

    if context.task_id != "context-task-001":
        raise RuntimeError(
            "Task ID is incorrect."
        )

    if not context.has_permission("read"):
        raise RuntimeError(
            "Permission should exist."
        )

    print("CREATE: PASS")

    # -------------------------------------------------
    # NON-STRING / EMPTY USER ID AND TASK ID
    # -------------------------------------------------
    #
    # create() is documented as producing a "validated"
    # execution context. A missing or non-string user_id/
    # task_id must be rejected with a clear ValueError,
    # never silently accepted or raise deep inside an
    # unrelated call.
    # -------------------------------------------------

    invalid_identity_cases = [
        {"user_id": None, "task_id": "t"},
        {"user_id": "", "task_id": "t"},
        {"user_id": "   ", "task_id": "t"},
        {"user_id": 123, "task_id": "t"},
        {"user_id": "u", "task_id": None},
        {"user_id": "u", "task_id": ""},
        {"user_id": "u", "task_id": "   "},
        {"user_id": "u", "task_id": 123},
    ]

    for kwargs in invalid_identity_cases:
        try:
            ExecutionContext.create(**kwargs)
        except ValueError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "create() raised unexpected exception for "
                f"{kwargs}: {type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"Invalid identity should be rejected: {kwargs}"
            )

    print("INVALID USER/TASK ID: PASS")

    # -------------------------------------------------
    # INVALID PERMISSIONS / METADATA TYPES
    # -------------------------------------------------

    for bad_permissions in (123, "not-a-set", ["a", "b"]):
        try:
            ExecutionContext.create(
                user_id="u",
                task_id="t",
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

    for bad_metadata in (123, "not-a-dict", ["a", "b"]):
        try:
            ExecutionContext.create(
                user_id="u",
                task_id="t",
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

    print("INVALID PERMISSIONS/METADATA TYPE: PASS")

    # -------------------------------------------------
    # IMMUTABILITY
    # -------------------------------------------------

    try:
        context.user_id = "modified"
    except (AttributeError, TypeError):
        print("IMMUTABILITY: PASS")
    else:
        raise RuntimeError(
            "ExecutionContext must be immutable."
        )

    # -------------------------------------------------
    # WITH_AGENT / WITH_WORKING_DIRECTORY
    # -------------------------------------------------

    with_agent = context.with_agent("agent-001")

    if with_agent.agent_id != "agent-001":
        raise RuntimeError(
            "Agent ID was not updated."
        )

    if context.agent_id is not None:
        raise RuntimeError(
            "Original context must remain unchanged."
        )

    if with_agent.execution_id != context.execution_id:
        raise RuntimeError(
            "Execution ID must remain stable."
        )

    with_dir = context.with_working_directory("./workspace")

    if with_dir.working_directory != "./workspace":
        raise RuntimeError(
            "Working directory was not updated."
        )

    if context.working_directory == with_dir.working_directory:
        raise RuntimeError(
            "Original context must not be modified."
        )

    print("WITH_AGENT / WITH_WORKING_DIRECTORY: PASS")

    print()
    print("=" * 60)
    print("CONTEXT: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
