from core.agent_runtime_manager import AgentRuntimeManager


def main() -> None:
    manager = AgentRuntimeManager()

    print("INITIAL COUNT:", manager.count())

    # Create first runtime.
    first = manager.get_or_create("agent-001")

    if first.is_failure():
        raise RuntimeError(
            "Could not create first runtime."
        )

    runtime_one = first.require_data()

    print(
        "CREATED:",
        runtime_one.agent_id,
    )

    print(
        "COUNT:",
        manager.count(),
    )

    if not manager.contains("agent-001"):
        raise RuntimeError(
            "Runtime should exist."
        )

    print("CONTAINS: PASS")

    # Request the same runtime again.
    second = manager.get_or_create("agent-001")

    if second.is_failure():
        raise RuntimeError(
            "Could not retrieve existing runtime."
        )

    runtime_two = second.require_data()

    if runtime_one is not runtime_two:
        raise RuntimeError(
            "Manager must return the same runtime instance."
        )

    print("SAME INSTANCE: PASS")

    # Get existing runtime.
    found = manager.get("agent-001")

    if found.is_failure():
        raise RuntimeError(
            "Existing runtime could not be retrieved."
        )

    print(
        "GET:",
        found.require_data().agent_id,
    )

    # Missing runtime.
    missing = manager.get("missing-agent")

    if missing.is_success():
        raise RuntimeError(
            "Missing runtime should return failure."
        )

    print(
        "MISSING LOOKUP:",
        missing.error.code,
    )

    # Create second runtime.
    second_agent = manager.get_or_create(
        "agent-002"
    )

    if second_agent.is_failure():
        raise RuntimeError(
            "Could not create second runtime."
        )

    print(
        "SECOND RUNTIME:",
        second_agent.require_data().agent_id,
    )

    print(
        "COUNT BEFORE CLEAR:",
        manager.count(),
    )

    # Remove one idle runtime.
    removed = manager.remove("agent-001")

    if removed.is_failure():
        raise RuntimeError(
            "Idle runtime should be removable."
        )

    print("REMOVE: PASS")

    print(
        "COUNT AFTER REMOVE:",
        manager.count(),
    )

    # Clear remaining idle runtimes.
    cleared = manager.clear_idle()

    print(
        "CLEARED:",
        cleared,
    )

    print(
        "FINAL COUNT:",
        manager.count(),
    )

    if manager.count() != 0:
        raise RuntimeError(
            "All idle runtimes should have been cleared."
        )

    print("AGENT RUNTIME MANAGER: PASS")


if __name__ == "__main__":
    main()