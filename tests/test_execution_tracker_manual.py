from core.execution_tracker import ExecutionTracker


def main() -> None:
    tracker = ExecutionTracker()

    # -------------------------------------------------
    # START EXECUTION
    # -------------------------------------------------

    progress = tracker.start(
        "execution-001",
        total_steps=4,
    )

    print(
        "EXECUTION ID:",
        progress.execution_id,
    )

    print(
        "STATUS:",
        progress.status,
    )

    print(
        "TOTAL STEPS:",
        progress.total_steps,
    )

    print(
        "PROGRESS:",
        progress.progress_percent,
    )

    if progress.status != "running":
        raise RuntimeError(
            "Execution should start in running state."
        )

    if progress.total_steps != 4:
        raise RuntimeError(
            "Total steps should be 4."
        )

    if progress.completed_steps != 0:
        raise RuntimeError(
            "Completed steps should start at 0."
        )

    if progress.progress_percent != 0.0:
        raise RuntimeError(
            "Initial progress should be 0%."
        )

    print("START: PASS")
    print("INITIAL PROGRESS: PASS")

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    tracker.start_step(
        "execution-001",
        "analyze",
    )

    current = tracker.get(
        "execution-001"
    )

    if current is None:
        raise RuntimeError(
            "Execution should be tracked."
        )

    print(
        "CURRENT STEP:",
        current.current_step,
    )

    if current.current_step != "analyze":
        raise RuntimeError(
            "Current step was not recorded."
        )

    tracker.complete_step(
        "execution-001",
        "analyze",
    )

    current = tracker.get(
        "execution-001"
    )

    if current.completed_steps != 1:
        raise RuntimeError(
            "Completed step count should be 1."
        )

    if current.progress_percent != 25.0:
        raise RuntimeError(
            "Progress should be 25%."
        )

    print(
        "STEP 1 PROGRESS:",
        current.progress_percent,
    )

    print("STEP 1: PASS")

    # -------------------------------------------------
    # STEP 2
    # -------------------------------------------------

    tracker.start_step(
        "execution-001",
        "design",
    )

    tracker.complete_step(
        "execution-001",
        "design",
    )

    current = tracker.get(
        "execution-001"
    )

    if current.completed_steps != 2:
        raise RuntimeError(
            "Completed step count should be 2."
        )

    if current.progress_percent != 50.0:
        raise RuntimeError(
            "Progress should be 50%."
        )

    print(
        "STEP 2 PROGRESS:",
        current.progress_percent,
    )

    print("STEP 2: PASS")

    # -------------------------------------------------
    # STEP 3
    # -------------------------------------------------

    tracker.start_step(
        "execution-001",
        "implement",
    )

    tracker.complete_step(
        "execution-001",
        "implement",
    )

    current = tracker.get(
        "execution-001"
    )

    if current.completed_steps != 3:
        raise RuntimeError(
            "Completed step count should be 3."
        )

    if current.progress_percent != 75.0:
        raise RuntimeError(
            "Progress should be 75%."
        )

    print(
        "STEP 3 PROGRESS:",
        current.progress_percent,
    )

    print("STEP 3: PASS")

    # -------------------------------------------------
    # STEP 4
    # -------------------------------------------------

    tracker.start_step(
        "execution-001",
        "test",
    )

    tracker.complete_step(
        "execution-001",
        "test",
    )

    current = tracker.get(
        "execution-001"
    )

    if current.completed_steps != 4:
        raise RuntimeError(
            "Completed step count should be 4."
        )

    if current.progress_percent != 100.0:
        raise RuntimeError(
            "Progress should be 100%."
        )

    if current.status != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    if current.current_step is not None:
        raise RuntimeError(
            "Current step should be cleared after completion."
        )

    print(
        "FINAL PROGRESS:",
        current.progress_percent,
    )

    print(
        "FINAL STATUS:",
        current.status,
    )

    print("STEP 4: PASS")
    print("COMPLETION: PASS")

    # -------------------------------------------------
    # FAILURE TRACKING
    # -------------------------------------------------

    tracker.start(
        "execution-002",
        total_steps=3,
    )

    tracker.start_step(
        "execution-002",
        "generate_code",
    )

    failed = tracker.fail(
        "execution-002",
        step_name="generate_code",
    )

    print(
        "FAILED STATUS:",
        failed.status,
    )

    print(
        "FAILED STEP:",
        failed.current_step,
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be marked failed."
        )

    if failed.current_step != "generate_code":
        raise RuntimeError(
            "Failed step should be preserved."
        )

    print("FAILURE TRACKING: PASS")

    # -------------------------------------------------
    # CANCEL TRACKING
    # -------------------------------------------------

    tracker.start(
        "execution-003",
        total_steps=2,
    )

    cancelled = tracker.cancel(
        "execution-003"
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    print("CANCEL TRACKING: PASS")

    # -------------------------------------------------
    # ACTIVE EXECUTIONS
    # -------------------------------------------------

    tracker.start(
        "execution-004",
        total_steps=1,
    )

    active = tracker.active()

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

    print("ACTIVE TRACKING: PASS")

    # -------------------------------------------------
    # DUPLICATE PROTECTION
    # -------------------------------------------------

    try:
        tracker.start(
            "execution-004",
            total_steps=1,
        )
    except ValueError:
        print("DUPLICATE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Duplicate execution should be rejected."
        )

    # -------------------------------------------------
    # INVALID STEP
    # -------------------------------------------------

    try:
        tracker.start_step(
            "execution-004",
            "   ",
        )
    except ValueError:
        print("INVALID STEP NAME: PASS")
    else:
        raise RuntimeError(
            "Empty step name should be rejected."
        )

    # -------------------------------------------------
    # UNKNOWN EXECUTION
    # -------------------------------------------------

    if tracker.get(
        "does-not-exist"
    ) is not None:
        raise RuntimeError(
            "Unknown execution should return None."
        )

    print("UNKNOWN EXECUTION: PASS")

    # -------------------------------------------------
    # CLEAR FINISHED
    # -------------------------------------------------

    removed = tracker.clear_finished()

    print(
        "CLEARED:",
        removed,
    )

    if tracker.get(
        "execution-001"
    ) is not None:
        raise RuntimeError(
            "Completed execution should be removed."
        )

    if tracker.get(
        "execution-002"
    ) is not None:
        raise RuntimeError(
            "Failed execution should be removed."
        )

    if tracker.get(
        "execution-003"
    ) is not None:
        raise RuntimeError(
            "Cancelled execution should be removed."
        )

    if tracker.get(
        "execution-004"
    ) is None:
        raise RuntimeError(
            "Running execution must remain tracked."
        )

    print("CLEAR FINISHED: PASS")

    print()
    print("=" * 60)
    print("EXECUTION TRACKER: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()