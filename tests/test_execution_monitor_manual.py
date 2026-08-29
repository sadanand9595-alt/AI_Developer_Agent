from core.execution_event_bus import ExecutionEventBus
from core.execution_monitor import ExecutionMonitor
from core.execution_tracker import ExecutionTracker


def main() -> None:
    tracker = ExecutionTracker()
    event_bus = ExecutionEventBus()

    monitor = ExecutionMonitor(
        tracker=tracker,
        event_bus=event_bus,
    )

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    progress = monitor.start(
        "execution-001",
        task_id="task-001",
        total_steps=4,
    )

    print(
        "START STATUS:",
        progress.status,
    )

    if progress.status != "running":
        raise RuntimeError(
            "Execution should start as running."
        )

    observation = monitor.get_observation(
        "execution-001"
    )

    if observation is None:
        raise RuntimeError(
            "Execution observation should exist."
        )

    if observation.status != "running":
        raise RuntimeError(
            "Observer should show running status."
        )

    if observation.total_steps != 4:
        raise RuntimeError(
            "Observer should track four steps."
        )

    print("START MONITORING: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    monitor.start_step(
        "execution-001",
        "analyze",
        task_id="task-001",
    )

    observation = monitor.get_observation(
        "execution-001"
    )

    if observation is None:
        raise RuntimeError(
            "Observation should exist."
        )

    if observation.current_step != "analyze":
        raise RuntimeError(
            "Current step should be analyze."
        )

    monitor.complete_step(
        "execution-001",
        "analyze",
        task_id="task-001",
    )

    progress = monitor.get_progress(
        "execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.completed_steps != 1:
        raise RuntimeError(
            "One step should be completed."
        )

    if progress.progress_percent != 25.0:
        raise RuntimeError(
            "Progress should be 25%."
        )

    print(
        "STEP 1 PROGRESS:",
        progress.progress_percent,
    )

    print("STEP 1 MONITORING: PASS")

    # -------------------------------------------------
    # STEP 2
    # -------------------------------------------------

    monitor.start_step(
        "execution-001",
        "design",
        task_id="task-001",
    )

    monitor.complete_step(
        "execution-001",
        "design",
        task_id="task-001",
    )

    progress = monitor.get_progress(
        "execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.progress_percent != 50.0:
        raise RuntimeError(
            "Progress should be 50%."
        )

    print(
        "STEP 2 PROGRESS:",
        progress.progress_percent,
    )

    print("STEP 2 MONITORING: PASS")

    # -------------------------------------------------
    # STEP 3
    # -------------------------------------------------

    monitor.start_step(
        "execution-001",
        "implement",
        task_id="task-001",
    )

    monitor.complete_step(
        "execution-001",
        "implement",
        task_id="task-001",
    )

    progress = monitor.get_progress(
        "execution-001"
    )

    if progress is None:
        raise RuntimeError(
            "Progress should exist."
        )

    if progress.progress_percent != 75.0:
        raise RuntimeError(
            "Progress should be 75%."
        )

    print(
        "STEP 3 PROGRESS:",
        progress.progress_percent,
    )

    print("STEP 3 MONITORING: PASS")

    # -------------------------------------------------
    # STEP 4 / AUTO COMPLETION
    # -------------------------------------------------

    monitor.start_step(
        "execution-001",
        "test",
        task_id="task-001",
    )

    progress = monitor.complete_step(
        "execution-001",
        "test",
        task_id="task-001",
    )

    if progress.progress_percent != 100.0:
        raise RuntimeError(
            "Progress should be 100%."
        )

    if progress.status != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    observation = monitor.get_observation(
        "execution-001"
    )

    if observation is None:
        raise RuntimeError(
            "Observation should exist."
        )

    if observation.status != "completed":
        raise RuntimeError(
            "Observer should show completed status."
        )

    if observation.progress_percent != 100.0:
        raise RuntimeError(
            "Observer progress should be 100%."
        )

    print(
        "FINAL PROGRESS:",
        progress.progress_percent,
    )

    print(
        "FINAL STATUS:",
        progress.status,
    )

    print("COMPLETION MONITORING: PASS")

    # -------------------------------------------------
    # FAILURE
    # -------------------------------------------------

    monitor.start(
        "execution-002",
        task_id="task-002",
        total_steps=2,
    )

    monitor.start_step(
        "execution-002",
        "generate_code",
        task_id="task-002",
    )

    failed = monitor.fail(
        "execution-002",
        task_id="task-002",
        step_name="generate_code",
        error_code="CODE_GENERATION_FAILED",
        error_message="Test failure.",
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    failed_observation = monitor.get_observation(
        "execution-002"
    )

    if failed_observation is None:
        raise RuntimeError(
            "Failed execution should be observed."
        )

    if failed_observation.status != "failed":
        raise RuntimeError(
            "Observer should show failed status."
        )

    if failed_observation.current_step != (
        "generate_code"
    ):
        raise RuntimeError(
            "Failed step should be preserved."
        )

    print(
        "FAILURE STATUS:",
        failed_observation.status,
    )

    print(
        "FAILURE STEP:",
        failed_observation.current_step,
    )

    print("FAILURE MONITORING: PASS")

    # -------------------------------------------------
    # CANCEL
    # -------------------------------------------------

    monitor.start(
        "execution-003",
        task_id="task-003",
        total_steps=3,
    )

    cancelled = monitor.cancel(
        "execution-003",
        task_id="task-003",
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    cancelled_observation = (
        monitor.get_observation(
            "execution-003"
        )
    )

    if cancelled_observation is None:
        raise RuntimeError(
            "Cancelled execution should be observed."
        )

    if cancelled_observation.status != (
        "cancelled"
    ):
        raise RuntimeError(
            "Observer should show cancelled status."
        )

    print(
        "CANCEL STATUS:",
        cancelled_observation.status,
    )

    print("CANCEL MONITORING: PASS")

    # -------------------------------------------------
    # ACTIVE PROGRESS
    # -------------------------------------------------

    monitor.start(
        "execution-004",
        task_id="task-004",
        total_steps=1,
    )

    active = monitor.active_progress()

    active_ids = {
        item.execution_id
        for item in active
    }

    if "execution-004" not in active_ids:
        raise RuntimeError(
            "Running execution should be active."
        )

    if "execution-001" in active_ids:
        raise RuntimeError(
            "Completed execution must not be active."
        )

    if "execution-002" in active_ids:
        raise RuntimeError(
            "Failed execution must not be active."
        )

    if "execution-003" in active_ids:
        raise RuntimeError(
            "Cancelled execution must not be active."
        )

    print("ACTIVE PROGRESS: PASS")

    # -------------------------------------------------
    # OBSERVATION COUNT
    # -------------------------------------------------

    if monitor.observation_count() != 4:
        raise RuntimeError(
            "Expected four observations."
        )

    print(
        "OBSERVATION COUNT:",
        monitor.observation_count(),
    )

    print("OBSERVATION COUNT: PASS")

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    monitor.close()

    # After close, no new events should be observed.
    monitor.start(
        "execution-005",
        task_id="task-005",
        total_steps=1,
    )

    if monitor.get_observation(
        "execution-005"
    ) is not None:
        raise RuntimeError(
            "Closed monitor must not receive new events."
        )

    print("CLOSE: PASS")

    print()
    print("=" * 60)
    print("EXECUTION MONITOR: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()