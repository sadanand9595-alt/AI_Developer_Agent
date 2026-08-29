from core.execution_audit import ExecutionAudit
from core.execution_audit_service import ExecutionAuditService
from core.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)


def main() -> None:
    audit = ExecutionAudit()

    service = ExecutionAuditService(
        audit
    )

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

    record = service.record_event(
        started
    )

    if record.execution_id != "execution-001":
        raise RuntimeError(
            "Execution ID was not recorded."
        )

    if record.event_type != (
        ExecutionEventType.STARTED
    ):
        raise RuntimeError(
            "Event type was not recorded."
        )

    print("RECORD EVENT: PASS")

    # -------------------------------------------------
    # RECORD DIRECTLY
    # -------------------------------------------------

    service.record(
        execution_id="execution-001",
        event_type=ExecutionEventType.STEP_STARTED,
        task_id="task-001",
        step_name="analyze",
        data={
            "step": 1,
        },
    )

    service.record(
        execution_id="execution-001",
        event_type=ExecutionEventType.STEP_COMPLETED,
        task_id="task-001",
        step_name="analyze",
        data={
            "progress": 33.33,
        },
    )

    service.record(
        execution_id="execution-002",
        event_type=ExecutionEventType.STARTED,
        task_id="task-002",
    )

    service.record(
        execution_id="execution-002",
        event_type=ExecutionEventType.FAILED,
        task_id="task-002",
        step_name="generate_code",
        data={
            "code": "ACTION_FAILED",
        },
    )

    print("DIRECT RECORDING: PASS")

    # -------------------------------------------------
    # GET EXECUTION
    # -------------------------------------------------

    execution_one = service.get_execution(
        "execution-001"
    )

    if len(execution_one) != 3:
        raise RuntimeError(
            "execution-001 should have three audit records."
        )

    if execution_one[0].event_type != (
        ExecutionEventType.STARTED
    ):
        raise RuntimeError(
            "Incorrect first execution event."
        )

    print("GET EXECUTION: PASS")

    # -------------------------------------------------
    # GET TASK
    # -------------------------------------------------

    task_one = service.get_task(
        "task-001"
    )

    if len(task_one) != 3:
        raise RuntimeError(
            "task-001 should have three records."
        )

    print("GET TASK: PASS")

    # -------------------------------------------------
    # GET EVENT TYPE
    # -------------------------------------------------

    failed_events = service.get_event_type(
        ExecutionEventType.FAILED
    )

    if len(failed_events) != 1:
        raise RuntimeError(
            "Expected one failed event."
        )

    if failed_events[0].execution_id != (
        "execution-002"
    ):
        raise RuntimeError(
            "Failed event belongs to wrong execution."
        )

    print("GET EVENT TYPE: PASS")

    # -------------------------------------------------
    # LIST ALL
    # -------------------------------------------------

    all_records = service.list_all()

    if len(all_records) != 5:
        raise RuntimeError(
            "Expected five audit records."
        )

    if service.count() != 5:
        raise RuntimeError(
            "Audit service count should be five."
        )

    print("LIST ALL: PASS")
    print(
        "AUDIT COUNT:",
        service.count(),
    )
    print("COUNT: PASS")

    # -------------------------------------------------
    # INVALID EVENT
    # -------------------------------------------------

    try:
        service.record_event(
            "invalid-event"
        )
    except TypeError:
        print("INVALID EVENT: PASS")
    else:
        raise RuntimeError(
            "Invalid event should be rejected."
        )

    # -------------------------------------------------
    # INVALID AUDIT REPOSITORY
    # -------------------------------------------------

    try:
        ExecutionAuditService(
            "invalid-audit"
        )
    except TypeError:
        print("INVALID AUDIT REPOSITORY: PASS")
    else:
        raise RuntimeError(
            "Invalid audit repository should be rejected."
        )

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    cleared = service.clear()

    if cleared != 5:
        raise RuntimeError(
            "Expected five records to be cleared."
        )

    if service.count() != 0:
        raise RuntimeError(
            "Audit service should be empty after clear."
        )

    print(
        "CLEARED:",
        cleared,
    )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION AUDIT SERVICE: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()