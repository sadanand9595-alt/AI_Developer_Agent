from core.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)


def main() -> None:
    # -------------------------------------------------
    # STARTED EVENT
    # -------------------------------------------------

    started = ExecutionEvent.create(
        event_type=ExecutionEventType.STARTED,
        execution_id="execution-001",
        task_id="task-001",
        data={
            "status": "running",
        },
    )

    print(
        "EVENT TYPE:",
        started.event_type,
    )

    print(
        "EXECUTION ID:",
        started.execution_id,
    )

    print(
        "TASK ID:",
        started.task_id,
    )

    print(
        "DATA:",
        started.data,
    )

    if not started.is_type(
        ExecutionEventType.STARTED
    ):
        raise RuntimeError(
            "Started event type is incorrect."
        )

    if started.is_terminal():
        raise RuntimeError(
            "Started event cannot be terminal."
        )

    print("STARTED EVENT: PASS")

    # -------------------------------------------------
    # STEP STARTED EVENT
    # -------------------------------------------------

    step_started = ExecutionEvent.create(
        event_type=ExecutionEventType.STEP_STARTED,
        execution_id="execution-001",
        task_id="task-001",
        step_name="analyze",
        data={
            "step_order": 1,
        },
    )

    print(
        "STEP EVENT:",
        step_started.event_type,
    )

    print(
        "STEP NAME:",
        step_started.step_name,
    )

    if not step_started.is_step_event():
        raise RuntimeError(
            "Step started event should be a step event."
        )

    if step_started.step_name != "analyze":
        raise RuntimeError(
            "Step name was not stored correctly."
        )

    print("STEP STARTED: PASS")

    # -------------------------------------------------
    # STEP COMPLETED EVENT
    # -------------------------------------------------

    step_completed = ExecutionEvent.create(
        event_type=ExecutionEventType.STEP_COMPLETED,
        execution_id="execution-001",
        task_id="task-001",
        step_name="analyze",
        data={
            "progress": 25.0,
        },
    )

    if not step_completed.is_step_event():
        raise RuntimeError(
            "Step completed event should be a step event."
        )

    if step_completed.data["progress"] != 25.0:
        raise RuntimeError(
            "Step event data was not stored."
        )

    print("STEP COMPLETED: PASS")

    # -------------------------------------------------
    # COMPLETED EVENT
    # -------------------------------------------------

    completed = ExecutionEvent.create(
        event_type=ExecutionEventType.COMPLETED,
        execution_id="execution-001",
        task_id="task-001",
        data={
            "status": "completed",
        },
    )

    if not completed.is_terminal():
        raise RuntimeError(
            "Completed event should be terminal."
        )

    print("COMPLETED EVENT: PASS")

    # -------------------------------------------------
    # FAILED EVENT
    # -------------------------------------------------

    failed = ExecutionEvent.create(
        event_type=ExecutionEventType.FAILED,
        execution_id="execution-002",
        task_id="task-002",
        step_name="generate_code",
        data={
            "code": "ACTION_FAILED",
            "message": "Code generation failed.",
        },
    )

    if not failed.is_terminal():
        raise RuntimeError(
            "Failed event should be terminal."
        )

    if failed.step_name != "generate_code":
        raise RuntimeError(
            "Failed step name was not preserved."
        )

    print("FAILED EVENT: PASS")

    # -------------------------------------------------
    # CANCELLED EVENT
    # -------------------------------------------------

    cancelled = ExecutionEvent.create(
        event_type=ExecutionEventType.CANCELLED,
        execution_id="execution-003",
        data={
            "reason": "User cancelled execution.",
        },
    )

    if not cancelled.is_terminal():
        raise RuntimeError(
            "Cancelled event should be terminal."
        )

    print("CANCELLED EVENT: PASS")

    # -------------------------------------------------
    # TIMESTAMP
    # -------------------------------------------------

    if started.timestamp is None:
        raise RuntimeError(
            "Event timestamp should exist."
        )

    print(
        "TIMESTAMP:",
        started.timestamp.isoformat(),
    )

    print("TIMESTAMP: PASS")

    # -------------------------------------------------
    # INVALID EVENT TYPE
    # -------------------------------------------------

    try:
        ExecutionEvent.create(
            event_type="   ",
            execution_id="execution-invalid",
        )
    except ValueError:
        print("INVALID EVENT TYPE: PASS")
    else:
        raise RuntimeError(
            "Empty event type should be rejected."
        )

    # -------------------------------------------------
    # INVALID EXECUTION ID
    # -------------------------------------------------

    try:
        ExecutionEvent.create(
            event_type=ExecutionEventType.STARTED,
            execution_id="   ",
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
        started.event_type = "modified"
    except (
        AttributeError,
        TypeError,
    ):
        print("IMMUTABILITY: PASS")
    else:
        raise RuntimeError(
            "ExecutionEvent should be immutable."
        )

    print()
    print("=" * 60)
    print("EXECUTION EVENT: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()