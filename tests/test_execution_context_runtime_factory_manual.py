from core.execution_context_runtime_factory import (
    ExecutionContextRuntimeFactory,
)
from core.execution_context_runtime_service import (
    ExecutionContextRuntimeService,
)


def main() -> None:
    # -------------------------------------------------
    # FACTORY CREATE
    # -------------------------------------------------

    service = ExecutionContextRuntimeFactory.create()

    if not isinstance(
        service,
        ExecutionContextRuntimeService,
    ):
        raise RuntimeError(
            "Factory must return ExecutionContextRuntimeService."
        )

    print("FACTORY CREATE: PASS")

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------

    if service.count() != 0:
        raise RuntimeError(
            "Factory-created service must start empty."
        )

    if service.ids():
        raise RuntimeError(
            "Factory-created service must have no runtime IDs."
        )

    print("INITIAL STATE: PASS")

    # -------------------------------------------------
    # CREATE RUNTIME
    # -------------------------------------------------

    runtime = service.create(
        "factory-runtime-001"
    )

    if runtime.context_id != (
        "factory-runtime-001"
    ):
        raise RuntimeError(
            "Runtime context ID is incorrect."
        )

    if not runtime.active:
        raise RuntimeError(
            "New runtime must be active."
        )

    if service.count() != 1:
        raise RuntimeError(
            "Expected one runtime."
        )

    print("CREATE RUNTIME: PASS")

    # -------------------------------------------------
    # RUNTIME OPERATION
    # -------------------------------------------------

    runtime.start_step(
        "factory-test-step"
    )

    runtime.complete_step()

    if runtime.completed_steps != 1:
        raise RuntimeError(
            "Runtime operation failed."
        )

    print("RUNTIME OPERATION: PASS")

    # -------------------------------------------------
    # FACTORY ISOLATION
    # -------------------------------------------------

    second_service = (
        ExecutionContextRuntimeFactory.create()
    )

    if second_service.count() != 0:
        raise RuntimeError(
            "Factory instances must be isolated."
        )

    if second_service.get(
        "factory-runtime-001"
    ) is not None:
        raise RuntimeError(
            "Runtime leaked into second factory instance."
        )

    print("FACTORY ISOLATION: PASS")

    # -------------------------------------------------
    # SECOND INSTANCE OPERATION
    # -------------------------------------------------

    second_runtime = second_service.create(
        "factory-runtime-002"
    )

    if second_service.count() != 1:
        raise RuntimeError(
            "Second service should contain one runtime."
        )

    if service.count() != 1:
        raise RuntimeError(
            "First service must remain isolated."
        )

    if second_runtime.context_id != (
        "factory-runtime-002"
    ):
        raise RuntimeError(
            "Second runtime ID is incorrect."
        )

    print("SECOND INSTANCE: PASS")

    # -------------------------------------------------
    # STOP FIRST
    # -------------------------------------------------

    stopped = service.stop(
        "factory-runtime-001"
    )

    if not stopped:
        raise RuntimeError(
            "First runtime should stop."
        )

    if runtime.active:
        raise RuntimeError(
            "First runtime must be inactive."
        )

    if second_runtime.active is not True:
        raise RuntimeError(
            "Second runtime must remain active."
        )

    print("STOP ISOLATION: PASS")

    # -------------------------------------------------
    # CLEAR SECOND
    # -------------------------------------------------

    cleared = second_service.clear()

    if cleared != 1:
        raise RuntimeError(
            "Expected one runtime to be cleared."
        )

    if second_service.count() != 0:
        raise RuntimeError(
            "Second service should be empty."
        )

    if second_runtime.active:
        raise RuntimeError(
            "Clear should stop the second runtime."
        )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION CONTEXT RUNTIME FACTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()