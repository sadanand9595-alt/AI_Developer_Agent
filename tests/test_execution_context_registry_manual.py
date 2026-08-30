from core.execution_context import ExecutionContext
from core.execution_context_registry import (
    ExecutionContextRegistry,
)


def main() -> None:
    registry = ExecutionContextRegistry()

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if registry.count() != 0:
        raise RuntimeError(
            "Registry must start empty."
        )

    if registry.ids():
        raise RuntimeError(
            "Registry IDs must initially be empty."
        )

    if registry.all():
        raise RuntimeError(
            "Registry contexts must initially be empty."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE CONTEXTS
    # -------------------------------------------------

    context_one = ExecutionContext.create(
        execution_id="registry-execution-001",
        task_id="registry-task-001",
        agent_id="agent-001",
    )

    context_two = ExecutionContext.create(
        execution_id="registry-execution-002",
        task_id="registry-task-002",
        agent_id="agent-002",
    )

    # -------------------------------------------------
    # REGISTER
    # -------------------------------------------------

    registry.register(context_one)
    registry.register(context_two)

    if registry.count() != 2:
        raise RuntimeError(
            "Registry should contain two contexts."
        )

    print(
        "REGISTER COUNT:",
        registry.count(),
    )

    print("REGISTER: PASS")

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    found = registry.get(
        context_one.context_id
    )

    if found is not context_one:
        raise RuntimeError(
            "get() returned the wrong context."
        )

    print("GET: PASS")

    # -------------------------------------------------
    # GET BY EXECUTION
    # -------------------------------------------------

    found_by_execution = (
        registry.get_by_execution(
            "registry-execution-002"
        )
    )

    if found_by_execution is not context_two:
        raise RuntimeError(
            "get_by_execution() returned the wrong context."
        )

    print("GET BY EXECUTION: PASS")

    # -------------------------------------------------
    # CONTAINS
    # -------------------------------------------------

    if not registry.contains(
        context_one.context_id
    ):
        raise RuntimeError(
            "Context one should be registered."
        )

    if not registry.contains(
        context_two.context_id
    ):
        raise RuntimeError(
            "Context two should be registered."
        )

    if registry.contains(
        "missing-context"
    ):
        raise RuntimeError(
            "Unknown context must not be registered."
        )

    print("CONTAINS: PASS")

    # -------------------------------------------------
    # IDS
    # -------------------------------------------------

    ids = registry.ids()

    if set(ids) != {
        context_one.context_id,
        context_two.context_id,
    }:
        raise RuntimeError(
            "Registry IDs are incorrect."
        )

    print(
        "IDS:",
        ids,
    )

    print("IDS: PASS")

    # -------------------------------------------------
    # ALL
    # -------------------------------------------------

    contexts = registry.all()

    if len(contexts) != 2:
        raise RuntimeError(
            "all() should return two contexts."
        )

    if context_one not in contexts:
        raise RuntimeError(
            "Context one missing from all()."
        )

    if context_two not in contexts:
        raise RuntimeError(
            "Context two missing from all()."
        )

    print("ALL: PASS")

    # -------------------------------------------------
    # TYPE VALIDATION
    # -------------------------------------------------

    try:
        registry.register(
            "invalid-context"
        )
    except TypeError:
        print("TYPE VALIDATION: PASS")
    else:
        raise RuntimeError(
            "Invalid context type should be rejected."
        )

    # -------------------------------------------------
    # DUPLICATE PROTECTION
    # -------------------------------------------------

    try:
        registry.register(
            context_one
        )
    except ValueError:
        print("DUPLICATE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Duplicate context should be rejected."
        )

    # -------------------------------------------------
    # UNKNOWN LOOKUP
    # -------------------------------------------------

    if registry.get(
        "missing-context"
    ) is not None:
        raise RuntimeError(
            "Unknown context lookup must return None."
        )

    if registry.get_by_execution(
        "missing-execution"
    ) is not None:
        raise RuntimeError(
            "Unknown execution lookup must return None."
        )

    print("UNKNOWN LOOKUP: PASS")

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    removed = registry.unregister(
        context_one.context_id
    )

    if not removed:
        raise RuntimeError(
            "Context one should be removed."
        )

    if registry.contains(
        context_one.context_id
    ):
        raise RuntimeError(
            "Removed context must not remain."
        )

    if registry.count() != 1:
        raise RuntimeError(
            "One context should remain."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNKNOWN UNREGISTER
    # -------------------------------------------------

    removed = registry.unregister(
        "missing-context"
    )

    if removed:
        raise RuntimeError(
            "Unknown context should not be removed."
        )

    print("UNKNOWN UNREGISTER: PASS")

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    cleared = registry.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one context to be cleared."
        )

    if registry.count() != 0:
        raise RuntimeError(
            "Registry should be empty after clear."
        )

    if registry.ids():
        raise RuntimeError(
            "Registry IDs should be empty after clear."
        )

    if registry.all():
        raise RuntimeError(
            "Registry contexts should be empty after clear."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    # -------------------------------------------------
    # NON-STRING ID (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------
    #
    # A non-string context_id/execution_id must be
    # rejected via each method's existing contract
    # (False/None), never raise an unrelated exception.
    # -------------------------------------------------

    for bad_id in (None, 123, ["not", "a", "string"]):
        try:
            unregister_result = registry.unregister(bad_id)
            get_result = registry.get(bad_id)
            get_by_execution_result = (
                registry.get_by_execution(bad_id)
            )
            contains_result = registry.contains(bad_id)
        except Exception as exc:
            raise RuntimeError(
                "Lookup method raised unexpected exception for "
                f"{bad_id!r}: {type(exc).__name__}: {exc}"
            )

        if unregister_result is not False:
            raise RuntimeError(
                f"unregister should return False for {bad_id!r}."
            )

        if get_result is not None:
            raise RuntimeError(
                f"get should return None for {bad_id!r}."
            )

        if get_by_execution_result is not None:
            raise RuntimeError(
                f"get_by_execution should return None for {bad_id!r}."
            )

        if contains_result is not False:
            raise RuntimeError(
                f"contains should return False for {bad_id!r}."
            )

    print("NON-STRING ID SAFETY: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT REGISTRY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()