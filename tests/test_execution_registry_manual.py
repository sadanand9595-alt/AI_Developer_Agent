from core.execution_registry import ExecutionRegistry


class FakeExecution:
    """Simple execution object for registry testing."""

    def __init__(
        self,
        execution_id: str,
    ) -> None:
        self.execution_id = execution_id


def main() -> None:
    registry = ExecutionRegistry()

    execution_one = FakeExecution(
        "execution-001"
    )

    execution_two = FakeExecution(
        "execution-002"
    )

    # -------------------------------------------------
    # REGISTER
    # -------------------------------------------------

    registry.register(
        "execution-001",
        execution_one,
    )

    registry.register(
        "execution-002",
        execution_two,
    )

    if registry.count() != 2:
        raise RuntimeError(
            "Registry should contain two executions."
        )

    print(
        "REGISTER COUNT:",
        registry.count(),
    )

    print("REGISTER: PASS")

    # -------------------------------------------------
    # CONTAINS
    # -------------------------------------------------

    if not registry.contains(
        "execution-001"
    ):
        raise RuntimeError(
            "execution-001 should be registered."
        )

    if not registry.contains(
        "execution-002"
    ):
        raise RuntimeError(
            "execution-002 should be registered."
        )

    if registry.contains(
        "execution-999"
    ):
        raise RuntimeError(
            "Unknown execution must not be registered."
        )

    print("CONTAINS: PASS")

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    result = registry.get(
        "execution-001"
    )

    if result is not execution_one:
        raise RuntimeError(
            "Registry returned the wrong execution."
        )

    if result.execution_id != (
        "execution-001"
    ):
        raise RuntimeError(
            "Execution ID is incorrect."
        )

    print("GET: PASS")

    # -------------------------------------------------
    # IDS
    # -------------------------------------------------

    ids = registry.ids()

    if set(ids) != {
        "execution-001",
        "execution-002",
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

    executions = registry.all()

    if len(executions) != 2:
        raise RuntimeError(
            "all() should return two executions."
        )

    if execution_one not in executions:
        raise RuntimeError(
            "execution_one should exist in all()."
        )

    if execution_two not in executions:
        raise RuntimeError(
            "execution_two should exist in all()."
        )

    print("ALL: PASS")

    # -------------------------------------------------
    # DUPLICATE PROTECTION
    # -------------------------------------------------

    try:
        registry.register(
            "execution-001",
            FakeExecution(
                "execution-001"
            ),
        )
    except ValueError:
        print("DUPLICATE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Duplicate execution should be rejected."
        )

    # -------------------------------------------------
    # EMPTY ID PROTECTION
    # -------------------------------------------------

    try:
        registry.register(
            "   ",
            execution_one,
        )
    except ValueError:
        print("EMPTY ID PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Empty execution ID should be rejected."
        )

    # -------------------------------------------------
    # NONE PROTECTION
    # -------------------------------------------------

    try:
        registry.register(
            "execution-003",
            None,
        )
    except ValueError:
        print("NONE EXECUTION PROTECTION: PASS")
    else:
        raise RuntimeError(
            "None execution should be rejected."
        )

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    removed = registry.unregister(
        "execution-001"
    )

    if not removed:
        raise RuntimeError(
            "execution-001 should be removed."
        )

    if registry.contains(
        "execution-001"
    ):
        raise RuntimeError(
            "Removed execution must not remain registered."
        )

    if registry.count() != 1:
        raise RuntimeError(
            "Registry should contain one execution."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNREGISTER UNKNOWN
    # -------------------------------------------------

    removed = registry.unregister(
        "execution-999"
    )

    if removed:
        raise RuntimeError(
            "Unknown execution should not be removed."
        )

    print("UNKNOWN UNREGISTER: PASS")

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    cleared = registry.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one execution to be cleared."
        )

    if registry.count() != 0:
        raise RuntimeError(
            "Registry should be empty."
        )

    if registry.ids():
        raise RuntimeError(
            "Registry IDs should be empty."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    # -------------------------------------------------
    # NON-STRING EXECUTION ID (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------
    #
    # A non-string execution_id must be rejected via each
    # method's existing contract (raise for register(),
    # False/None for the lookup methods), never raise an
    # unrelated AttributeError.
    # -------------------------------------------------

    for bad_id in (None, 123, ["not", "a", "string"]):
        try:
            registry.register(
                bad_id,
                FakeExecution("x"),
            )
        except ValueError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "register raised unexpected exception for "
                f"{bad_id!r}: {type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"register should reject non-string id {bad_id!r}."
            )

        try:
            unregister_result = registry.unregister(bad_id)
            get_result = registry.get(bad_id)
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

        if contains_result is not False:
            raise RuntimeError(
                f"contains should return False for {bad_id!r}."
            )

    print("NON-STRING EXECUTION ID SAFETY: PASS")

    print()
    print("=" * 60)
    print("EXECUTION REGISTRY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()