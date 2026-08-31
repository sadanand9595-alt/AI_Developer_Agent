"""
Manual integration test for ExecutionCoordinator
and ExecutionContextRuntimeApplication.
"""

from core.action_registry import ActionRegistry
from core.execution_coordinator import ExecutionCoordinator


def main() -> None:
    coordinator = ExecutionCoordinator(
        registry_service=None,
    )

    execution_id = "integration-runtime-001"

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    record = coordinator.start(
        execution_id,
        task_id="task-integration-001",
        total_steps=2,
        metadata={
            "source": "manual-integration-test",
        },
    )

    if record.execution_id != execution_id:
        raise RuntimeError(
            "Execution ID mismatch."
        )

    if coordinator.get_runtime(execution_id) is None:
        raise RuntimeError(
            "Context runtime was not created."
        )

    print("START + RUNTIME CREATE: PASS")

    # -------------------------------------------------
    # RUNTIME SNAPSHOT AFTER START
    # -------------------------------------------------

    snapshot = coordinator.get_runtime_snapshot(
        execution_id
    )

    if snapshot.get("context_id") != execution_id:
        raise RuntimeError(
            "Runtime snapshot context ID mismatch."
        )

    print("RUNTIME SNAPSHOT: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    progress = coordinator.start_step(
        execution_id,
        "integration-step-1",
        task_id="task-integration-001",
    )

    if progress.current_step != "integration-step-1":
        raise RuntimeError(
            "Execution step was not started."
        )

    runtime = coordinator.get_runtime(
        execution_id
    )

    if runtime is None:
        raise RuntimeError(
            "Runtime disappeared after step start."
        )

    if runtime.current_step != "integration-step-1":
        raise RuntimeError(
            "Runtime current step was not synchronized."
        )

    print("STEP 1 SYNCHRONIZATION: PASS")

    # -------------------------------------------------
    # COMPLETE STEP 1
    # -------------------------------------------------

    progress = coordinator.complete_step(
        execution_id,
        "integration-step-1",
        task_id="task-integration-001",
    )

    if progress.completed_steps != 1:
        raise RuntimeError(
            "Execution completed-step count is incorrect."
        )

    runtime = coordinator.get_runtime(
        execution_id
    )

    if runtime is None:
        raise RuntimeError(
            "Runtime disappeared after step completion."
        )

    if runtime.completed_steps != 1:
        raise RuntimeError(
            "Runtime completed-step count is incorrect."
        )

    print("STEP 1 COMPLETION SYNCHRONIZATION: PASS")

    # -------------------------------------------------
    # STEP 2
    # -------------------------------------------------

    coordinator.start_step(
        execution_id,
        "integration-step-2",
        task_id="task-integration-001",
    )

    runtime = coordinator.get_runtime(
        execution_id
    )

    if runtime is None:
        raise RuntimeError(
            "Runtime disappeared before step 2."
        )

    if runtime.current_step != "integration-step-2":
        raise RuntimeError(
            "Runtime did not track step 2."
        )

    print("STEP 2 START: PASS")

    # -------------------------------------------------
    # COMPLETE EXECUTION
    # -------------------------------------------------

    record = coordinator.complete(
        execution_id,
        output={
            "result": "integration-success",
        },
    )

    if record.status != "completed":
        raise RuntimeError(
            "Execution was not completed."
        )

    if coordinator.get_runtime(
        execution_id
    ) is not None:
        raise RuntimeError(
            "Runtime was not cleaned up after completion."
        )

    if coordinator.is_registered(
        execution_id
    ):
        raise RuntimeError(
            "Execution remained registered after completion."
        )

    print("COMPLETE + RUNTIME CLEANUP: PASS")

    # -------------------------------------------------
    # FAILURE PATH
    # -------------------------------------------------

    failed_execution_id = (
        "integration-runtime-failure-001"
    )

    coordinator.start(
        failed_execution_id,
        task_id="task-integration-failure",
        total_steps=1,
    )

    coordinator.start_step(
        failed_execution_id,
        "failing-step",
        task_id="task-integration-failure",
    )

    if coordinator.get_runtime(
        failed_execution_id
    ) is None:
        raise RuntimeError(
            "Failure-path runtime was not created."
        )

    failed_record = coordinator.fail(
        failed_execution_id,
        error_code="INTEGRATION_TEST_FAILURE",
        error_message="Expected integration failure.",
        step_name="failing-step",
    )

    if failed_record.status != "failed":
        raise RuntimeError(
            "Failure execution did not enter failed state."
        )

    if coordinator.get_runtime(
        failed_execution_id
    ) is not None:
        raise RuntimeError(
            "Failure runtime was not cleaned up."
        )

    if coordinator.is_registered(
        failed_execution_id
    ):
        raise RuntimeError(
            "Failed execution remained registered."
        )

    print("FAILURE + RUNTIME CLEANUP: PASS")

    # -------------------------------------------------
    # AUTO-COMPLETION VIA complete_step() (NO complete() CALL)
    # -------------------------------------------------
    #
    # Reaching 100% through complete_step() alone (never calling
    # complete()) must clean up the context runtime exactly like
    # complete() does. Regression test for a bug where only the
    # execution registry was cleaned up, permanently orphaning an
    # active ExecutionContextRuntime.
    # -------------------------------------------------

    auto_complete_id = "integration-runtime-auto-complete-001"

    coordinator.start(
        auto_complete_id,
        task_id="task-integration-auto-complete",
        total_steps=1,
    )

    coordinator.start_step(
        auto_complete_id,
        "only-step",
        task_id="task-integration-auto-complete",
    )

    auto_progress = coordinator.complete_step(
        auto_complete_id,
        "only-step",
        task_id="task-integration-auto-complete",
    )

    if auto_progress.status != "completed":
        raise RuntimeError(
            "Single-step execution should auto-complete."
        )

    if coordinator.get_runtime(
        auto_complete_id
    ) is not None:
        raise RuntimeError(
            "Context runtime was not cleaned up after "
            "complete_step() auto-completion."
        )

    if coordinator.is_registered(
        auto_complete_id
    ):
        raise RuntimeError(
            "Auto-completed execution remained registered."
        )

    print("AUTO-COMPLETION RUNTIME CLEANUP: PASS")

    # -------------------------------------------------
    # ISOLATION
    # -------------------------------------------------

    if coordinator.active_count() != 0:
        raise RuntimeError(
            "No executions should remain active."
        )

    print("EXECUTION ISOLATION: PASS")

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    coordinator.close()

    print("CLOSE: PASS")

    print()
    print("=" * 60)
    print(
        "EXECUTION COORDINATOR RUNTIME INTEGRATION: PASS"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()