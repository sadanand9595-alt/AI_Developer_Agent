from core.execution_context_runtime_application import (
    ExecutionContextRuntimeApplication,
)
from core.execution_context_runtime_application_factory import (
    ExecutionContextRuntimeApplicationFactory,
)


def main() -> None:
    # -------------------------------------------------
    # FACTORY CREATE
    # -------------------------------------------------

    application = (
        ExecutionContextRuntimeApplicationFactory.create()
    )

    if not isinstance(
        application,
        ExecutionContextRuntimeApplication,
    ):
        raise RuntimeError(
            "Factory must return "
            "ExecutionContextRuntimeApplication."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if application.count() != 0:
        raise RuntimeError(
            "Factory-created application must start empty."
        )

    if application.ids():
        raise RuntimeError(
            "Factory-created application must have no IDs."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    runtime = application.create(
        "factory-runtime-application-001"
    )

    if runtime.context_id != (
        "factory-runtime-application-001"
    ):
        raise RuntimeError(
            "Runtime context ID is incorrect."
        )

    if not runtime.active:
        raise RuntimeError(
            "New runtime must be active."
        )

    if application.count() != 1:
        raise RuntimeError(
            "Expected one runtime."
        )

    print("CREATE: PASS")

    # -------------------------------------------------
    # STEP
    # -------------------------------------------------

    application.start_step(
        "factory-runtime-application-001",
        "execute",
    )

    application.complete_step(
        "factory-runtime-application-001"
    )

    if runtime.completed_steps != 1:
        raise RuntimeError(
            "Completed step count should be one."
        )

    print("STEP: PASS")

    # -------------------------------------------------
    # VARIABLE
    # -------------------------------------------------

    application.set_variable(
        "factory-runtime-application-001",
        "status",
        "running",
    )

    if application.get_variable(
        "factory-runtime-application-001",
        "status",
    ) != "running":
        raise RuntimeError(
            "Runtime variable was not preserved."
        )

    print("VARIABLE: PASS")

    # -------------------------------------------------
    # SNAPSHOT
    # -------------------------------------------------

    snapshot = application.snapshot(
        "factory-runtime-application-001"
    )

    if snapshot["context_id"] != (
        "factory-runtime-application-001"
    ):
        raise RuntimeError(
            "Snapshot context ID is incorrect."
        )

    if snapshot["completed_steps"] != 1:
        raise RuntimeError(
            "Snapshot completed steps are incorrect."
        )

    if snapshot["variables"].get(
        "status"
    ) != "running":
        raise RuntimeError(
            "Snapshot variable is incorrect."
        )

    print("SNAPSHOT: PASS")

    # -------------------------------------------------
    # FACTORY ISOLATION
    # -------------------------------------------------

    second = (
        ExecutionContextRuntimeApplicationFactory.create()
    )

    if second.count() != 0:
        raise RuntimeError(
            "Factory instances must be isolated."
        )

    if second.get(
        "factory-runtime-application-001"
    ) is not None:
        raise RuntimeError(
            "Runtime leaked into second application."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # SECOND INSTANCE
    # -------------------------------------------------

    second_runtime = second.create(
        "factory-runtime-application-002"
    )

    if second.count() != 1:
        raise RuntimeError(
            "Second application should contain one runtime."
        )

    if application.count() != 1:
        raise RuntimeError(
            "First application must remain isolated."
        )

    if not second_runtime.active:
        raise RuntimeError(
            "Second runtime must be active."
        )

    print("SECOND INSTANCE: PASS")

    # -------------------------------------------------
    # STOP ISOLATION
    # -------------------------------------------------

    if not application.stop(
        "factory-runtime-application-001"
    ):
        raise RuntimeError(
            "First runtime should stop."
        )

    if runtime.active:
        raise RuntimeError(
            "First runtime must be inactive."
        )

    if not second_runtime.active:
        raise RuntimeError(
            "Second runtime must remain active."
        )

    print("STOP ISOLATION: PASS")

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    cleared = second.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one runtime to be cleared."
        )

    if second.count() != 0:
        raise RuntimeError(
            "Second application should be empty."
        )

    if second_runtime.active:
        raise RuntimeError(
            "Clear should stop the runtime."
        )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print(
        "EXECUTION CONTEXT RUNTIME APPLICATION FACTORY: PASS"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()