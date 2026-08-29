from core.action_registry import ActionRegistry
from core.result import Result


def analyze_handler(value):
    return Result.ok(
        {
            "action": "analyze_requirements",
            "value": value,
        }
    )


def code_handler(value):
    return Result.ok(
        {
            "action": "generate_code",
            "value": value,
        }
    )


def main() -> None:
    registry = ActionRegistry()

    print("INITIAL COUNT:", registry.count())

    if registry.count() != 0:
        raise RuntimeError(
            "Registry should start empty."
        )

    # Register first action.
    registered = registry.register(
        "analyze_requirements",
        analyze_handler,
    )

    if registered.is_failure():
        raise RuntimeError(
            registered.error.message
        )

    print("REGISTER ANALYZE: PASS")

    # Register second action.
    registered = registry.register(
        "generate_code",
        code_handler,
    )

    if registered.is_failure():
        raise RuntimeError(
            registered.error.message
        )

    print("REGISTER CODE: PASS")

    print(
        "ACTIONS:",
        registry.list_actions(),
    )

    print(
        "COUNT:",
        registry.count(),
    )

    if registry.count() != 2:
        raise RuntimeError(
            "Registry should contain two actions."
        )

    # Contains.
    if not registry.contains(
        "analyze_requirements"
    ):
        raise RuntimeError(
            "Registered action should exist."
        )

    print("CONTAINS: PASS")

    # Get handler.
    handler_result = registry.get(
        "analyze_requirements"
    )

    if handler_result.is_failure():
        raise RuntimeError(
            handler_result.error.message
        )

    handler = handler_result.require_data()

    result = handler(
        "CRM requirements"
    )

    if result.is_failure():
        raise RuntimeError(
            result.error.message
        )

    print(
        "HANDLER RESULT:",
        result.require_data(),
    )

    print("GET HANDLER: PASS")

    # Duplicate registration.
    duplicate = registry.register(
        "analyze_requirements",
        analyze_handler,
    )

    if duplicate.is_success():
        raise RuntimeError(
            "Duplicate action should be rejected."
        )

    print(
        "DUPLICATE:",
        duplicate.error.code,
    )

    if duplicate.error.code != (
        "ACTION_ALREADY_REGISTERED"
    ):
        raise RuntimeError(
            "Unexpected duplicate error."
        )

    print("DUPLICATE PROTECTION: PASS")

    # Replace handler.
    replacement = registry.register(
        "analyze_requirements",
        code_handler,
        replace=True,
    )

    if replacement.is_failure():
        raise RuntimeError(
            replacement.error.message
        )

    print("REPLACE: PASS")

    # Missing action.
    missing = registry.get(
        "missing_action"
    )

    if missing.is_success():
        raise RuntimeError(
            "Missing action should fail."
        )

    print(
        "MISSING:",
        missing.error.code,
    )

    if missing.error.code != "ACTION_NOT_FOUND":
        raise RuntimeError(
            "Unexpected missing action error."
        )

    print("MISSING ACTION: PASS")

    # Unregister.
    removed = registry.unregister(
        "generate_code"
    )

    if removed.is_failure():
        raise RuntimeError(
            removed.error.message
        )

    print("UNREGISTER: PASS")

    if registry.contains(
        "generate_code"
    ):
        raise RuntimeError(
            "Removed action should not exist."
        )

    # Clear.
    registry.clear()

    if registry.count() != 0:
        raise RuntimeError(
            "Registry should be empty after clear."
        )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("ACTION REGISTRY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()