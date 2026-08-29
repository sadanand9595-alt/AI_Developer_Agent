from core.execution_registry import ExecutionRegistry
from core.execution_registry_service import (
    ExecutionRegistryService,
)


class FakeExecution:
    """Simple execution object for testing."""

    def __init__(
        self,
        execution_id: str,
    ) -> None:
        self.execution_id = execution_id


def main() -> None:
    registry = ExecutionRegistry()

    service = ExecutionRegistryService(
        registry
    )

    execution_one = FakeExecution(
        "execution-001"
    )

    execution_two = FakeExecution(
        "execution-002"
    )

    # -------------------------------------------------
    # SERVICE CREATION
    # -------------------------------------------------

    if not isinstance(
        service,
        ExecutionRegistryService,
    ):
        raise RuntimeError(
            "Service creation failed."
        )

    print("SERVICE CREATE: PASS")

    # -------------------------------------------------
    # REGISTER
    # -------------------------------------------------

    service.register(
        "execution-001",
        execution_one,
    )

    service.register(
        "execution-002",
        execution_two,
    )

    if service.count() != 2:
        raise RuntimeError(
            "Expected two registered executions."
        )

    print(
        "REGISTER COUNT:",
        service.count(),
    )

    print("REGISTER: PASS")

    # -------------------------------------------------
    # CONTAINS
    # -------------------------------------------------

    if not service.contains(
        "execution-001"
    ):
        raise RuntimeError(
            "execution-001 should be registered."
        )

    if not service.contains(
        "execution-002"
    ):
        raise RuntimeError(
            "execution-002 should be registered."
        )

    if service.contains(
        "execution-999"
    ):
        raise RuntimeError(
            "Unknown execution should not exist."
        )

    print("CONTAINS: PASS")

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    result = service.get(
        "execution-001"
    )

    if result is not execution_one:
        raise RuntimeError(
            "Incorrect execution returned."
        )

    if result.execution_id != (
        "execution-001"
    ):
        raise RuntimeError(
            "Incorrect execution ID."
        )

    print("GET: PASS")

    # -------------------------------------------------
    # IDS
    # -------------------------------------------------

    ids = service.ids()

    if set(ids) != {
        "execution-001",
        "execution-002",
    }:
        raise RuntimeError(
            "Incorrect execution IDs."
        )

    print(
        "IDS:",
        ids,
    )

    print("IDS: PASS")

    # -------------------------------------------------
    # ALL
    # -------------------------------------------------

    executions = service.all()

    if len(executions) != 2:
        raise RuntimeError(
            "Expected two executions."
        )

    if execution_one not in executions:
        raise RuntimeError(
            "execution_one missing."
        )

    if execution_two not in executions:
        raise RuntimeError(
            "execution_two missing."
        )

    print("ALL: PASS")

    # -------------------------------------------------
    # DUPLICATE PROTECTION
    # -------------------------------------------------

    try:
        service.register(
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
    # INVALID SERVICE DEPENDENCY
    # -------------------------------------------------

    try:
        ExecutionRegistryService(
            "invalid-registry"
        )
    except TypeError:
        print(
            "INVALID REGISTRY DEPENDENCY: PASS"
        )
    else:
        raise RuntimeError(
            "Invalid registry should be rejected."
        )

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    removed = service.unregister(
        "execution-001"
    )

    if not removed:
        raise RuntimeError(
            "execution-001 should be removed."
        )

    if service.contains(
        "execution-001"
    ):
        raise RuntimeError(
            "Removed execution still exists."
        )

    if service.count() != 1:
        raise RuntimeError(
            "Expected one remaining execution."
        )

    print("UNREGISTER: PASS")

    # -------------------------------------------------
    # UNKNOWN UNREGISTER
    # -------------------------------------------------

    removed = service.unregister(
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

    cleared = service.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one execution to be cleared."
        )

    if service.count() != 0:
        raise RuntimeError(
            "Registry should be empty."
        )

    if service.ids():
        raise RuntimeError(
            "Execution IDs should be empty."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION REGISTRY SERVICE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()