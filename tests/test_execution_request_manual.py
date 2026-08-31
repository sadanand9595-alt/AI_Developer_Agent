from core.execution_request import ExecutionRequest


def main() -> None:
    request = ExecutionRequest.create(
        request="Create a production-ready CRM application.",
        user_id="user-001",
        task_id="task-001",
        agent_id="agent-001",
        session_id="session-001",
        conversation_id="conversation-001",
        workspace_root="D:\\AI_COMMAND_CENTER",
        working_directory="D:\\AI_COMMAND_CENTER",
        permissions={
            "read",
            "write",
            "execute",
        },
        metadata={
            "priority": "high",
            "source": "manual-test",
        },
    )

    print("REQUEST:", request.request)
    print("USER:", request.user_id)
    print("TASK:", request.task_id)
    print("AGENT:", request.agent_id)
    print("WORKSPACE:", request.workspace_root)
    print("PERMISSIONS:", request.permissions)
    print("METADATA:", request.metadata)

    if request.request != (
        "Create a production-ready CRM application."
    ):
        raise RuntimeError(
            "Request was not stored correctly."
        )

    if request.user_id != "user-001":
        raise RuntimeError(
            "User ID was not stored correctly."
        )

    if not request.has_permission("read"):
        raise RuntimeError(
            "Read permission should exist."
        )

    if not request.has_permission("write"):
        raise RuntimeError(
            "Write permission should exist."
        )

    if not request.has_permission("execute"):
        raise RuntimeError(
            "Execute permission should exist."
        )

    print("REQUEST CREATION: PASS")
    print("PERMISSIONS: PASS")

    # Immutable metadata update.
    updated = request.with_metadata(
        "environment",
        "test",
    )

    if request.has_permission(
        "environment"
    ):
        raise RuntimeError(
            "Metadata must not affect permissions."
        )

    if request.metadata.get(
        "environment"
    ) is not None:
        raise RuntimeError(
            "Original request must remain unchanged."
        )

    if updated.metadata.get(
        "environment"
    ) != "test":
        raise RuntimeError(
            "Updated metadata was not stored."
        )

    print("IMMUTABILITY: PASS")
    print("METADATA UPDATE: PASS")

    # Empty request protection.
    try:
        ExecutionRequest.create(
            request="   ",
        )
    except ValueError:
        print("EMPTY REQUEST PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Empty request should be rejected."
        )

    # Empty metadata key protection.
    try:
        request.with_metadata(
            "",
            "invalid",
        )
    except ValueError:
        print("INVALID METADATA KEY: PASS")
    else:
        raise RuntimeError(
            "Empty metadata key should be rejected."
        )

    # Permission isolation.
    if request.has_permission(
        "admin"
    ):
        raise RuntimeError(
            "Unexpected permission detected."
        )

    print("PERMISSION ISOLATION: PASS")

    for bad_kwargs in (
        {"request": 123},
        {"request": "x", "workspace_root": 123},
        {"request": "x", "working_directory": 123},
    ):
        try:
            ExecutionRequest.create(**bad_kwargs)
        except ValueError:
            pass
        else:
            raise RuntimeError(
                f"Non-string field {bad_kwargs!r} should be rejected."
            )

    valid_request = ExecutionRequest.create(request="valid")

    try:
        valid_request.with_metadata(123, "value")
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "Non-string metadata key should be rejected."
        )

    print("NON-STRING FIELD SAFETY: PASS")

    print()
    print("=" * 60)
    print("EXECUTION REQUEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()