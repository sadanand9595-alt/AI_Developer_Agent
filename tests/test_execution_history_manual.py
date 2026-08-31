from core.execution_history import ExecutionHistory


def main() -> None:
    history = ExecutionHistory()

    # -------------------------------------------------
    # RECORD COMPLETED EXECUTION
    # -------------------------------------------------

    completed = history.record(
        "execution-001",
        status="completed",
        task_id="task-001",
        output={
            "status": "success",
            "files": 5,
        },
        metadata={
            "engine": "execution-engine",
        },
    )

    print(
        "RECORDED:",
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
            "Output was not stored correctly."
        )

    print("RECORD COMPLETED: PASS")

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    stored = history.get(
        "execution-001"
    )

    if stored is None:
        raise RuntimeError(
            "History record should exist."
        )

    if stored.execution_id != "execution-001":
        raise RuntimeError(
            "Execution ID was not stored correctly."
        )

    if stored.task_id != "task-001":
        raise RuntimeError(
            "Task ID was not stored correctly."
        )

    print("GET: PASS")

    # -------------------------------------------------
    # RECORD FAILURE
    # -------------------------------------------------

    failed = history.record(
        "execution-002",
        status="failed",
        task_id="task-002",
        error_code="ACTION_FAILED",
        error_message="Test action failed.",
        metadata={
            "retryable": True,
        },
    )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    if failed.error_code != "ACTION_FAILED":
        raise RuntimeError(
            "Incorrect error code."
        )

    if failed.error_message != (
        "Test action failed."
    ):
        raise RuntimeError(
            "Incorrect error message."
        )

    print("RECORD FAILURE: PASS")

    # -------------------------------------------------
    # RECORD CANCELLED
    # -------------------------------------------------

    cancelled = history.record(
        "execution-003",
        status="cancelled",
        task_id="task-003",
        metadata={
            "reason": "user_cancelled",
        },
    )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    print("RECORD CANCELLED: PASS")

    # -------------------------------------------------
    # COUNT
    # -------------------------------------------------

    if history.count() != 3:
        raise RuntimeError(
            "Expected three history records."
        )

    print(
        "HISTORY COUNT:",
        history.count(),
    )

    print("COUNT: PASS")

    # -------------------------------------------------
    # LIST ALL
    # -------------------------------------------------

    records = history.list_all()

    if len(records) != 3:
        raise RuntimeError(
            "list_all() should return three records."
        )

    print("LIST ALL: PASS")

    # -------------------------------------------------
    # LIST BY STATUS
    # -------------------------------------------------

    completed_records = (
        history.list_by_status(
            "completed"
        )
    )

    if len(completed_records) != 1:
        raise RuntimeError(
            "Expected one completed record."
        )

    failed_records = (
        history.list_by_status(
            "failed"
        )
    )

    if len(failed_records) != 1:
        raise RuntimeError(
            "Expected one failed record."
        )

    cancelled_records = (
        history.list_by_status(
            "cancelled"
        )
    )

    if len(cancelled_records) != 1:
        raise RuntimeError(
            "Expected one cancelled record."
        )

    print("FILTER BY STATUS: PASS")

    # -------------------------------------------------
    # LIST BY TASK
    # -------------------------------------------------

    task_records = history.list_by_task(
        "task-002"
    )

    if len(task_records) != 1:
        raise RuntimeError(
            "Expected one record for task-002."
        )

    if task_records[0].execution_id != (
        "execution-002"
    ):
        raise RuntimeError(
            "Incorrect task history record."
        )

    print("FILTER BY TASK: PASS")

    # -------------------------------------------------
    # DUPLICATE PROTECTION
    # -------------------------------------------------

    try:
        history.record(
            "execution-001",
            status="completed",
        )
    except ValueError:
        print("DUPLICATE PROTECTION: PASS")
    else:
        raise RuntimeError(
            "Duplicate execution should be rejected."
        )

    # -------------------------------------------------
    # NON-TERMINAL STATUS PROTECTION
    # -------------------------------------------------

    try:
        history.record(
            "execution-004",
            status="running",
        )
    except ValueError:
        print("NON-TERMINAL STATUS: PASS")
    else:
        raise RuntimeError(
            "Running status should not be recorded."
        )

    # -------------------------------------------------
    # INVALID EXECUTION ID
    # -------------------------------------------------

    try:
        history.record(
            "   ",
            status="completed",
        )
    except ValueError:
        print("INVALID EXECUTION ID: PASS")
    else:
        raise RuntimeError(
            "Empty execution ID should be rejected."
        )

    # -------------------------------------------------
    # IMMUTABILITY
    # -------------------------------------------------

    try:
        completed.status = "failed"
    except (
        AttributeError,
        TypeError,
    ):
        print("IMMUTABILITY: PASS")
    else:
        raise RuntimeError(
            "History record should be immutable."
        )

    # -------------------------------------------------
    # REMOVE
    # -------------------------------------------------

    removed = history.remove(
        "execution-003"
    )

    if not removed:
        raise RuntimeError(
            "Execution should be removed."
        )

    if history.get(
        "execution-003"
    ) is not None:
        raise RuntimeError(
            "Removed record should not exist."
        )

    print("REMOVE: PASS")

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    removed_count = history.clear()

    if removed_count != 2:
        raise RuntimeError(
            "Expected two remaining records to be cleared."
        )

    if history.count() != 0:
        raise RuntimeError(
            "History should be empty after clear."
        )

    print(
        "CLEARED:",
        removed_count,
    )

    print("CLEAR: PASS")

    # -------------------------------------------------
    # NON-STRING ID/KEY (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------

    for bad_value in (None, 123, ["not", "a", "string"]):
        try:
            history.record(
                bad_value,
                status="completed",
            )
        except ValueError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "record() raised unexpected exception for "
                f"execution_id={bad_value!r}: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"record() should reject execution_id={bad_value!r}."
            )

        try:
            history.record(
                "history-bad-status",
                status=bad_value,
            )
        except ValueError:
            pass
        except Exception as exc:
            raise RuntimeError(
                "record() raised unexpected exception for "
                f"status={bad_value!r}: {type(exc).__name__}: {exc}"
            )
        else:
            raise RuntimeError(
                f"record() should reject status={bad_value!r}."
            )

        try:
            get_result = history.get(bad_value)
            status_result = history.list_by_status(bad_value)
            task_result = history.list_by_task(bad_value)
            remove_result = history.remove(bad_value)
        except Exception as exc:
            raise RuntimeError(
                "Lookup method raised unexpected exception for "
                f"{bad_value!r}: {type(exc).__name__}: {exc}"
            )

        if get_result is not None:
            raise RuntimeError(
                f"get should return None for {bad_value!r}."
            )

        if status_result != ():
            raise RuntimeError(
                f"list_by_status should return () for {bad_value!r}."
            )

        if task_result != ():
            raise RuntimeError(
                f"list_by_task should return () for {bad_value!r}."
            )

        if remove_result is not False:
            raise RuntimeError(
                f"remove should return False for {bad_value!r}."
            )

    print("NON-STRING ID/KEY SAFETY: PASS")

    # -------------------------------------------------
    # METADATA MUTATION ISOLATION
    # -------------------------------------------------
    #
    # A caller mutating the metadata dict on a returned
    # record must not corrupt the internally stored
    # "immutable-style historical snapshot".
    # -------------------------------------------------

    isolation_history = ExecutionHistory()

    returned = isolation_history.record(
        "isolation-001",
        status="completed",
        metadata={"a": 1},
    )

    returned.metadata["a"] = "corrupted"
    returned.metadata["injected"] = True

    fetched = isolation_history.get("isolation-001")
    fetched.metadata["also-corrupted"] = True

    for listed in isolation_history.list_all():
        listed.metadata["from-list-all"] = True

    final = isolation_history.get("isolation-001")

    if final.metadata != {"a": 1}:
        raise RuntimeError(
            "External mutation of a returned record's metadata "
            f"leaked into the stored history: {final.metadata}"
        )

    print("METADATA MUTATION ISOLATION: PASS")

    print()
    print("=" * 60)
    print("EXECUTION HISTORY: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()