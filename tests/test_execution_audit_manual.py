from core.execution_audit import ExecutionAudit
from core.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)


def main() -> None:
    audit = ExecutionAudit()

    # -------------------------------------------------
    # RECORD EVENT
    # -------------------------------------------------

    started = ExecutionEvent.create(
        event_type=ExecutionEventType.STARTED,
        execution_id="execution-001",
        task_id="task-001",
        data={
            "total_steps": 3,
        },
    )

    record = audit.record(started)

    print(
        "EXECUTION ID:",
        record.execution_id,
    )

    print(
        "EVENT TYPE:",
        record.event_type,
    )

    if record.execution_id != "execution-001":
        raise RuntimeError(
            "Execution ID was not recorded correctly."
        )

    if record.event_type != (
        ExecutionEventType.STARTED
    ):
        raise RuntimeError(
            "Event type was not recorded correctly."
        )

    print("RECORD EVENT: PASS")

    # -------------------------------------------------
    # STEP EVENTS
    # -------------------------------------------------

    audit.record(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STEP_STARTED,
            execution_id="execution-001",
            task_id="task-001",
            step_name="analyze",
        )
    )

    audit.record(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STEP_COMPLETED,
            execution_id="execution-001",
            task_id="task-001",
            step_name="analyze",
            data={
                "progress": 33.33,
            },
        )
    )

    audit.record(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STEP_STARTED,
            execution_id="execution-001",
            task_id="task-001",
            step_name="generate",
        )
    )

    print("STEP EVENTS: PASS")

    # -------------------------------------------------
    # COMPLETED EVENT
    # -------------------------------------------------

    audit.record(
        ExecutionEvent.create(
            event_type=ExecutionEventType.COMPLETED,
            execution_id="execution-001",
            task_id="task-001",
            data={
                "status": "completed",
            },
        )
    )

    # -------------------------------------------------
    # SECOND EXECUTION
    # -------------------------------------------------

    audit.record(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STARTED,
            execution_id="execution-002",
            task_id="task-002",
        )
    )

    audit.record(
        ExecutionEvent.create(
            event_type=ExecutionEventType.FAILED,
            execution_id="execution-002",
            task_id="task-002",
            step_name="generate",
            data={
                "code": "ACTION_FAILED",
            },
        )
    )

    # -------------------------------------------------
    # COUNT
    # -------------------------------------------------

    if audit.count() != 7:
        raise RuntimeError(
            "Expected seven audit records."
        )

    print(
        "AUDIT COUNT:",
        audit.count(),
    )

    print("COUNT: PASS")

    # -------------------------------------------------
    # LIST ALL
    # -------------------------------------------------

    records = audit.list_all()

    if len(records) != 7:
        raise RuntimeError(
            "list_all() should return seven records."
        )

    print("LIST ALL: PASS")

    # -------------------------------------------------
    # BY EXECUTION
    # -------------------------------------------------

    execution_one = (
        audit.list_by_execution(
            "execution-001"
        )
    )

    if len(execution_one) != 5:
        raise RuntimeError(
            "execution-001 should have five audit records."
        )

    execution_two = (
        audit.list_by_execution(
            "execution-002"
        )
    )

    if len(execution_two) != 2:
        raise RuntimeError(
            "execution-002 should have two audit records."
        )

    print("FILTER BY EXECUTION: PASS")

    # -------------------------------------------------
    # BY EVENT TYPE
    # -------------------------------------------------

    started_events = (
        audit.list_by_event_type(
            ExecutionEventType.STARTED
        )
    )

    if len(started_events) != 2:
        raise RuntimeError(
            "Expected two started events."
        )

    completed_events = (
        audit.list_by_event_type(
            ExecutionEventType.COMPLETED
        )
    )

    if len(completed_events) != 1:
        raise RuntimeError(
            "Expected one completed event."
        )

    failed_events = (
        audit.list_by_event_type(
            ExecutionEventType.FAILED
        )
    )

    if len(failed_events) != 1:
        raise RuntimeError(
            "Expected one failed event."
        )

    print("FILTER BY EVENT TYPE: PASS")

    # -------------------------------------------------
    # BY TASK
    # -------------------------------------------------

    task_one = audit.list_by_task(
        "task-001"
    )

    if len(task_one) != 5:
        raise RuntimeError(
            "task-001 should have five records."
        )

    task_two = audit.list_by_task(
        "task-002"
    )

    if len(task_two) != 2:
        raise RuntimeError(
            "task-002 should have two records."
        )

    print("FILTER BY TASK: PASS")

    # -------------------------------------------------
    # DIRECT VALUE RECORDING
    # -------------------------------------------------

    direct = audit.record_values(
        execution_id="execution-003",
        event_type="custom.event",
        task_id="task-003",
        step_name="custom_step",
        data={
            "source": "manual-test",
        },
    )

    if direct.execution_id != "execution-003":
        raise RuntimeError(
            "Direct execution ID is incorrect."
        )

    if direct.event_type != "custom.event":
        raise RuntimeError(
            "Direct event type is incorrect."
        )

    if direct.step_name != "custom_step":
        raise RuntimeError(
            "Direct step name is incorrect."
        )

    if direct.data["source"] != "manual-test":
        raise RuntimeError(
            "Direct event data is incorrect."
        )

    print("DIRECT RECORDING: PASS")

    # -------------------------------------------------
    # INVALID EVENT
    # -------------------------------------------------

    try:
        audit.record(
            "invalid-event"
        )
    except TypeError:
        print("INVALID EVENT: PASS")
    else:
        raise RuntimeError(
            "Invalid event should be rejected."
        )

    # -------------------------------------------------
    # INVALID DIRECT RECORD
    # -------------------------------------------------

    try:
        audit.record_values(
            execution_id="   ",
            event_type="test.event",
        )
    except ValueError:
        print("INVALID EXECUTION ID: PASS")
    else:
        raise RuntimeError(
            "Empty execution ID should be rejected."
        )

    try:
        audit.record_values(
            execution_id="execution-004",
            event_type="   ",
        )
    except ValueError:
        print("INVALID EVENT TYPE: PASS")
    else:
        raise RuntimeError(
            "Empty event type should be rejected."
        )

    # -------------------------------------------------
    # IMMUTABILITY
    # -------------------------------------------------

    try:
        record.event_type = "modified"
    except (
        AttributeError,
        TypeError,
    ):
        print("IMMUTABILITY: PASS")
    else:
        raise RuntimeError(
            "Audit record should be immutable."
        )

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    cleared = audit.clear()

    if cleared != 8:
        raise RuntimeError(
            "Expected eight audit records to be cleared."
        )

    if audit.count() != 0:
        raise RuntimeError(
            "Audit trail should be empty."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION AUDIT: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()