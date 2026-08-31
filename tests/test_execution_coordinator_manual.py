from core.execution_coordinator import ExecutionCoordinator
from core.pipeline_context import PipelineContext
from core.planner import ExecutionPlan


def main() -> None:
    coordinator = ExecutionCoordinator()

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    record = coordinator.start(
        "coordinator-execution-001",
        task_id="coordinator-task-001",
        total_steps=2,
        metadata={
            "source": "coordinator-test",
        },
    )

    if record.status != "running":
        raise RuntimeError(
            "Execution should be running."
        )

    if not coordinator.is_registered(
        "coordinator-execution-001"
    ):
        raise RuntimeError(
            "Execution should be registered."
        )

    if coordinator.registered_count() != 1:
        raise RuntimeError(
            "Expected one registered execution."
        )

    print("START: PASS")
    print("REGISTRATION: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    coordinator.start_step(
        "coordinator-execution-001",
        "analyze",
        task_id="coordinator-task-001",
    )

    coordinator.complete_step(
        "coordinator-execution-001",
        "analyze",
        task_id="coordinator-task-001",
    )

    progress = coordinator.get_progress(
        "coordinator-execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.completed_steps != 1:
        raise RuntimeError(
            "Expected one completed step."
        )

    if progress.progress_percent != 50.0:
        raise RuntimeError(
            "Progress should be 50%."
        )

    if not coordinator.is_registered(
        "coordinator-execution-001"
    ):
        raise RuntimeError(
            "Execution should remain registered."
        )

    print(
        "STEP 1 PROGRESS:",
        progress.progress_percent,
    )

    print("STEP 1: PASS")

    # -------------------------------------------------
    # STEP 2 / AUTO UNREGISTER
    # -------------------------------------------------

    coordinator.start_step(
        "coordinator-execution-001",
        "generate",
        task_id="coordinator-task-001",
    )

    coordinator.complete_step(
        "coordinator-execution-001",
        "generate",
        task_id="coordinator-task-001",
    )

    progress = coordinator.get_progress(
        "coordinator-execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.progress_percent != 100.0:
        raise RuntimeError(
            "Progress should be 100%."
        )

    if progress.status != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    if coordinator.is_registered(
        "coordinator-execution-001"
    ):
        raise RuntimeError(
            "Completed execution should be unregistered."
        )

    if coordinator.registered_count() != 0:
        raise RuntimeError(
            "Registry should be empty after completion."
        )

    print(
        "FINAL PROGRESS:",
        progress.progress_percent,
    )

    print(
        "FINAL STATUS:",
        progress.status,
    )

    print("AUTO UNREGISTER: PASS")

    # -------------------------------------------------
    # OBSERVATION
    # -------------------------------------------------

    observation = coordinator.get_observation(
        "coordinator-execution-001"
    )

    if observation is None:
        raise RuntimeError(
            "Observation should exist."
        )

    if observation.status != "completed":
        raise RuntimeError(
            "Observer should report completed."
        )

    if observation.progress_percent != 100.0:
        raise RuntimeError(
            "Observer progress should be 100%."
        )

    print("OBSERVATION: PASS")

    # -------------------------------------------------
    # AUDIT
    # -------------------------------------------------

    audit = coordinator.get_audit(
        "coordinator-execution-001"
    )

    if not audit:
        raise RuntimeError(
            "Audit records should exist."
        )

    audit_types = {
        item.event_type
        for item in audit
    }

    required_events = {
        "execution.started",
        "execution.step_started",
        "execution.step_completed",
        "execution.completed",
    }

    missing = required_events - audit_types

    if missing:
        raise RuntimeError(
            f"Missing audit events: {sorted(missing)}"
        )

    print(
        "AUDIT EVENTS:",
        sorted(audit_types),
    )

    print("AUDIT: PASS")

    # -------------------------------------------------
    # FAILURE
    # -------------------------------------------------

    coordinator.start(
        "coordinator-execution-002",
        task_id="coordinator-task-002",
        total_steps=1,
    )

    if not coordinator.is_registered(
        "coordinator-execution-002"
    ):
        raise RuntimeError(
            "Failed execution should initially be registered."
        )

    coordinator.start_step(
        "coordinator-execution-002",
        "generate_code",
        task_id="coordinator-task-002",
    )

    failed = coordinator.fail(
        "coordinator-execution-002",
        error_code="GENERATION_FAILED",
        error_message="Coordinator test failure.",
        step_name="generate_code",
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    if coordinator.is_registered(
        "coordinator-execution-002"
    ):
        raise RuntimeError(
            "Failed execution should be unregistered."
        )

    failed_observation = (
        coordinator.get_observation(
            "coordinator-execution-002"
        )
    )

    if failed_observation is None:
        raise RuntimeError(
            "Failed observation should exist."
        )

    if failed_observation.status != "failed":
        raise RuntimeError(
            "Observer should report failed."
        )

    print("FAILURE: PASS")

    # -------------------------------------------------
    # CANCEL
    # -------------------------------------------------

    coordinator.start(
        "coordinator-execution-003",
        task_id="coordinator-task-003",
        total_steps=1,
    )

    cancelled = coordinator.cancel(
        "coordinator-execution-003"
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    if coordinator.is_registered(
        "coordinator-execution-003"
    ):
        raise RuntimeError(
            "Cancelled execution should be unregistered."
        )

    cancelled_observation = (
        coordinator.get_observation(
            "coordinator-execution-003"
        )
    )

    if cancelled_observation is None:
        raise RuntimeError(
            "Cancelled observation should exist."
        )

    if cancelled_observation.status != "cancelled":
        raise RuntimeError(
            "Observer should report cancelled."
        )

    print("CANCEL: PASS")

    # -------------------------------------------------
    # REGISTERED IDS
    # -------------------------------------------------

    if coordinator.registered_count() != 0:
        raise RuntimeError(
            "No terminal execution should remain registered."
        )

    if coordinator.registered_ids():
        raise RuntimeError(
            "Registered IDs should be empty."
        )

    print("REGISTERED IDS: PASS")

    # -------------------------------------------------
    # ACTIVE COUNT
    # -------------------------------------------------

    if coordinator.active_count() != 0:
        raise RuntimeError(
            "No terminal execution should remain active."
        )

    print("ACTIVE COUNT: PASS")

    # -------------------------------------------------
    # AUDIT COUNT
    # -------------------------------------------------

    if coordinator.audit_count() <= 0:
        raise RuntimeError(
            "Audit records should exist."
        )

    print(
        "AUDIT COUNT:",
        coordinator.audit_count(),
    )

    print("AUDIT COUNT: PASS")

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    coordinator.close()

    print("CLOSE: PASS")

    # -------------------------------------------------
    # ZERO-STEP PLAN COMPLETION
    # -------------------------------------------------

    coordinator2 = ExecutionCoordinator()

    zero_step_plan = ExecutionPlan(
        plan_id="zero-step-plan",
        request="zero-step-request",
        steps=(),
        metadata={},
    )

    zero_step_context = PipelineContext(
        execution_id="coordinator-execution-zero",
        task_id="coordinator-task-zero",
    )

    zero_result = coordinator2.execute_plan(
        plan=zero_step_plan,
        context=zero_step_context,
    )

    if zero_result.is_failure():
        raise RuntimeError(
            "Zero-step plan execution should succeed."
        )

    zero_record = coordinator2.get(
        "coordinator-execution-zero"
    )

    if zero_record is None or zero_record.status != "completed":
        raise RuntimeError(
            "Zero-step execution should be completed."
        )

    if coordinator2.is_registered(
        "coordinator-execution-zero"
    ):
        raise RuntimeError(
            "Zero-step execution should be unregistered "
            "after completion."
        )

    print("ZERO-STEP PLAN: PASS")

    # -------------------------------------------------
    # DUPLICATE EXECUTION AFTER COMPLETION (REUSED ID)
    # -------------------------------------------------
    #
    # The execution manager retains completed/failed/cancelled
    # records even after the coordinator's registry has been
    # unregistered. Re-running the same execution_id must be
    # rejected with a clear EXECUTION_ALREADY_REGISTERED error
    # rather than an opaque failure surfacing from deep inside
    # the execution manager.
    # -------------------------------------------------

    reused_context = PipelineContext(
        execution_id="coordinator-execution-zero",
        task_id="coordinator-task-zero",
    )

    duplicate_result = coordinator2.execute_plan(
        plan=zero_step_plan,
        context=reused_context,
    )

    if duplicate_result.is_success():
        raise RuntimeError(
            "Reusing a completed execution_id should fail."
        )

    if duplicate_result.error.code != "EXECUTION_ALREADY_REGISTERED":
        raise RuntimeError(
            "Reused execution_id should be rejected as "
            "already registered, got: "
            f"{duplicate_result.error.code}"
        )

    print("DUPLICATE AFTER COMPLETION: PASS")

    coordinator2.close()

    # -------------------------------------------------
    # INVALID DEPENDENCIES (CONSTRUCTOR VALIDATION)
    # -------------------------------------------------

    for kwarg in (
        "registry",
        "facade",
        "registry_service",
        "planning_pipeline",
        "plan_executor",
        "runtime_application",
    ):
        try:
            ExecutionCoordinator(**{kwarg: "not-valid"})
        except TypeError:
            pass
        else:
            raise RuntimeError(
                f"Invalid {kwarg} should be rejected."
            )

    print("INVALID DEPENDENCIES: PASS")

    print()
    print("=" * 60)
    print("EXECUTION COORDINATOR: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()