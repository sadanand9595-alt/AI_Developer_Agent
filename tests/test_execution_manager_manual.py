from core.execution_manager import ExecutionManager


def main() -> None:
    manager = ExecutionManager()

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    record = manager.start(
        "execution-001",
        task_id="task-001",
        metadata={
            "source": "manual-test",
        },
    )

    print("STARTED:", record.execution_id)
    print("STATUS:", record.status)
    print("TASK:", record.task_id)

    if record.status != "running":
        raise RuntimeError(
            "New execution should be running."
        )

    if manager.count() != 1:
        raise RuntimeError(
            "Expected one tracked execution."
        )

    if manager.active_count() != 1:
        raise RuntimeError(
            "Expected one active execution."
        )

    print("START: PASS")
    print("ACTIVE TRACKING: PASS")

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    stored = manager.get(
        "execution-001"
    )

    if stored is None:
        raise RuntimeError(
            "Execution record should exist."
        )

    if stored.execution_id != "execution-001":
        raise RuntimeError(
            "Execution ID was not stored correctly."
        )

    print("GET: PASS")

    # -------------------------------------------------
    # COMPLETE
    # -------------------------------------------------

    completed = manager.complete(
        "execution-001",
        output={
            "status": "success",
            "files": 5,
        },
        metadata={
            "duration_ms": 1200,
        },
    )

    print(
        "COMPLETED:",
        completed.execution_id,
    )
    print(
        "STATUS:",
        completed.status,
    )
    print(
        "OUTPUT:",
        completed.output,
    )

    if completed.status != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    if completed.output["files"] != 5:
        raise RuntimeError(
            "Execution output was not stored."
        )

    if completed.completed_at is None:
        raise RuntimeError(
            "Completion timestamp should exist."
        )

    if manager.active_count() != 0:
        raise RuntimeError(
            "Completed execution must not remain active."
        )

    print("COMPLETE: PASS")
    print("TERMINAL STATE: PASS")

    # -------------------------------------------------
    # SECOND EXECUTION — FAILURE
    # -------------------------------------------------

    manager.start(
        "execution-002",
        task_id="task-002",
    )

    failed = manager.fail(
        "execution-002",
        error_code="TEST_FAILURE",
        error_message="Simulated execution failure.",
    )

    print(
        "FAILED:",
        failed.execution_id,
    )
    print(
        "STATUS:",
        failed.status,
    )
    print(
        "ERROR CODE:",
        failed.error_code,
    )
    print(
        "ERROR MESSAGE:",
        failed.error_message,
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    if failed.error_code != "TEST_FAILURE":
        raise RuntimeError(
            "Incorrect error code."
        )

    print("FAILURE: PASS")

    # -------------------------------------------------
    # THIRD EXECUTION — CANCEL
    # -------------------------------------------------

    manager.start(
        "execution-003",
        task_id="task-003",
    )

    cancelled = manager.cancel(
        "execution-003"
    )

    print(
        "CANCELLED:",
        cancelled.execution_id,
    )
    print(
        "STATUS:",
        cancelled.status,
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    print("CANCEL: PASS")

    # -------------------------------------------------
    # DUPLICATE EXECUTION
    # -------------------------------------------------

    try:
        manager.start(
            "execution-003"
        )
    except ValueError:
        print("DUPLICATE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Duplicate execution should be rejected."
        )

    # -------------------------------------------------
    # UNKNOWN EXECUTION
    # -------------------------------------------------

    if manager.get(
        "does-not-exist"
    ) is not None:
        raise RuntimeError(
            "Unknown execution should return None."
        )

    print("UNKNOWN EXECUTION: PASS")

    # -------------------------------------------------
    # TERMINAL STATE PROTECTION
    # -------------------------------------------------

    try:
        manager.complete(
            "execution-001"
        )
    except ValueError:
        print("TERMINAL STATE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Terminal execution should not be completed again."
        )

    # -------------------------------------------------
    # INVALID ERROR
    # -------------------------------------------------

    manager.start(
        "execution-004"
    )

    try:
        manager.fail(
            "execution-004",
            error_code="   ",
            error_message="Failure",
        )
    except ValueError:
        print("INVALID ERROR CODE: PASS")
    else:
        raise RuntimeError(
            "Empty error code should be rejected."
        )

    try:
        manager.fail(
            "execution-004",
            error_code="TEST",
            error_message="   ",
        )
    except ValueError:
        print("INVALID ERROR MESSAGE: PASS")
    else:
        raise RuntimeError(
            "Empty error message should be rejected."
        )

    # Clean up execution-004.
    manager.cancel(
        "execution-004"
    )

    # -------------------------------------------------
    # CLEAR COMPLETED
    # -------------------------------------------------

    removed = manager.clear_completed()

    print(
        "CLEARED TERMINAL RECORDS:",
        removed,
    )

    if manager.count() != 0:
        raise RuntimeError(
            "All terminal executions should be cleared."
        )

    print("CLEAR COMPLETED: PASS")

    print()
    print("=" * 60)
    print("EXECUTION MANAGER: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()