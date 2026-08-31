from core.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)
from core.execution_event_bus import ExecutionEventBus
from core.execution_observer import ExecutionObserver


def main() -> None:
    bus = ExecutionEventBus()
    observer = ExecutionObserver(bus)

    # -------------------------------------------------
    # STARTED
    # -------------------------------------------------

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STARTED,
            execution_id="execution-001",
            task_id="task-001",
            data={
                "total_steps": 4,
            },
        )
    )

    observation = observer.get(
        "execution-001"
    )

    if observation is None:
        raise RuntimeError(
            "Execution observation should exist."
        )

    print(
        "STATUS:",
        observation.status,
    )

    print(
        "TOTAL STEPS:",
        observation.total_steps,
    )

    print(
        "EVENTS:",
        observation.events_received,
    )

    if observation.status != "running":
        raise RuntimeError(
            "Started event should set running status."
        )

    if observation.total_steps != 4:
        raise RuntimeError(
            "Total steps should be 4."
        )

    if observation.events_received != 1:
        raise RuntimeError(
            "Expected one received event."
        )

    print("START OBSERVATION: PASS")

    # -------------------------------------------------
    # STEP STARTED
    # -------------------------------------------------

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STEP_STARTED,
            execution_id="execution-001",
            task_id="task-001",
            step_name="analyze",
        )
    )

    observation = observer.get(
        "execution-001"
    )

    if observation.current_step != "analyze":
        raise RuntimeError(
            "Current step should be analyze."
        )

    if observation.events_received != 2:
        raise RuntimeError(
            "Expected two received events."
        )

    print(
        "CURRENT STEP:",
        observation.current_step,
    )

    print("STEP STARTED: PASS")

    # -------------------------------------------------
    # STEP COMPLETED
    # -------------------------------------------------

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STEP_COMPLETED,
            execution_id="execution-001",
            task_id="task-001",
            step_name="analyze",
        )
    )

    observation = observer.get(
        "execution-001"
    )

    if observation.completed_steps != 1:
        raise RuntimeError(
            "Completed steps should be 1."
        )

    if observation.progress_percent != 25.0:
        raise RuntimeError(
            "Progress should be 25%."
        )

    print(
        "COMPLETED STEPS:",
        observation.completed_steps,
    )

    print(
        "PROGRESS:",
        observation.progress_percent,
    )

    print("STEP COMPLETED: PASS")

    # -------------------------------------------------
    # SECOND STEP
    # -------------------------------------------------

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STEP_STARTED,
            execution_id="execution-001",
            task_id="task-001",
            step_name="design",
        )
    )

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STEP_COMPLETED,
            execution_id="execution-001",
            task_id="task-001",
            step_name="design",
        )
    )

    observation = observer.get(
        "execution-001"
    )

    if observation.completed_steps != 2:
        raise RuntimeError(
            "Completed steps should be 2."
        )

    if observation.progress_percent != 50.0:
        raise RuntimeError(
            "Progress should be 50%."
        )

    print(
        "PROGRESS AFTER STEP 2:",
        observation.progress_percent,
    )

    print("STEP 2: PASS")

    # -------------------------------------------------
    # COMPLETED
    # -------------------------------------------------

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.COMPLETED,
            execution_id="execution-001",
            task_id="task-001",
        )
    )

    observation = observer.get(
        "execution-001"
    )

    if observation.status != "completed":
        raise RuntimeError(
            "Execution should be completed."
        )

    if observation.completed_steps != 4:
        raise RuntimeError(
            "Completed steps should equal total steps."
        )

    if observation.progress_percent != 100.0:
        raise RuntimeError(
            "Completed execution should be 100%."
        )

    if observation.current_step is not None:
        raise RuntimeError(
            "Current step should be cleared."
        )

    print(
        "FINAL STATUS:",
        observation.status,
    )

    print(
        "FINAL PROGRESS:",
        observation.progress_percent,
    )

    print("COMPLETION OBSERVATION: PASS")

    # -------------------------------------------------
    # FAILURE
    # -------------------------------------------------

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STARTED,
            execution_id="execution-002",
            task_id="task-002",
            data={
                "total_steps": 2,
            },
        )
    )

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STEP_STARTED,
            execution_id="execution-002",
            task_id="task-002",
            step_name="generate_code",
        )
    )

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.FAILED,
            execution_id="execution-002",
            task_id="task-002",
            step_name="generate_code",
        )
    )

    failed = observer.get(
        "execution-002"
    )

    if failed is None:
        raise RuntimeError(
            "Failed execution should be observed."
        )

    if failed.status != "failed":
        raise RuntimeError(
            "Execution should be failed."
        )

    if failed.current_step != "generate_code":
        raise RuntimeError(
            "Failed step should be preserved."
        )

    print(
        "FAILED STATUS:",
        failed.status,
    )

    print(
        "FAILED STEP:",
        failed.current_step,
    )

    print("FAILURE OBSERVATION: PASS")

    # -------------------------------------------------
    # CANCELLED
    # -------------------------------------------------

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STARTED,
            execution_id="execution-003",
            task_id="task-003",
            data={
                "total_steps": 3,
            },
        )
    )

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.CANCELLED,
            execution_id="execution-003",
            task_id="task-003",
        )
    )

    cancelled = observer.get(
        "execution-003"
    )

    if cancelled is None:
        raise RuntimeError(
            "Cancelled execution should be observed."
        )

    if cancelled.status != "cancelled":
        raise RuntimeError(
            "Execution should be cancelled."
        )

    print(
        "CANCELLED STATUS:",
        cancelled.status,
    )

    print("CANCEL OBSERVATION: PASS")

    # -------------------------------------------------
    # COUNT / ALL
    # -------------------------------------------------

    if observer.count() != 3:
        raise RuntimeError(
            "Expected three observations."
        )

    if len(observer.all()) != 3:
        raise RuntimeError(
            "all() should return three observations."
        )

    print("COUNT: PASS")
    print("ALL: PASS")

    # -------------------------------------------------
    # REMOVE
    # -------------------------------------------------

    removed = observer.remove(
        "execution-003"
    )

    if not removed:
        raise RuntimeError(
            "Execution should be removed."
        )

    if observer.get(
        "execution-003"
    ) is not None:
        raise RuntimeError(
            "Removed execution should not exist."
        )

    print("REMOVE: PASS")

    # -------------------------------------------------
    # CLOSE / UNSUBSCRIBE
    # -------------------------------------------------

    observer.close()

    bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STARTED,
            execution_id="execution-004",
            task_id="task-004",
            data={
                "total_steps": 1,
            },
        )
    )

    if observer.get(
        "execution-004"
    ) is not None:
        raise RuntimeError(
            "Closed observer must not receive events."
        )

    print("CLOSE / UNSUBSCRIBE: PASS")

    # -------------------------------------------------
    # NON-STRING EXECUTION ID (PUBLIC BOUNDARY SAFETY)
    # -------------------------------------------------

    type_check_observer = ExecutionObserver(
        ExecutionEventBus()
    )

    for bad_id in (None, 123, ["not", "a", "string"]):
        try:
            get_result = type_check_observer.get(bad_id)
            remove_result = type_check_observer.remove(bad_id)
        except Exception as exc:
            raise RuntimeError(
                "get/remove raised unexpected exception for "
                f"{bad_id!r}: {type(exc).__name__}: {exc}"
            )

        if get_result is not None:
            raise RuntimeError(
                f"get should return None for {bad_id!r}."
            )

        if remove_result is not False:
            raise RuntimeError(
                f"remove should return False for {bad_id!r}."
            )

    type_check_observer.close()

    print("NON-STRING EXECUTION ID SAFETY: PASS")

    # -------------------------------------------------
    # UNNORMALIZED EXECUTION ID KEY CONSISTENCY
    # -------------------------------------------------
    #
    # A directly-constructed ExecutionEvent (bypassing
    # create()'s own normalization) with surrounding
    # whitespace in execution_id must not be stored under
    # a key that get()'s normalized lookup can never match.
    # -------------------------------------------------

    isolation_observer = ExecutionObserver(
        ExecutionEventBus()
    )

    unnormalized_event = ExecutionEvent(
        event_type=ExecutionEventType.STARTED,
        execution_id="  execution-unnormalized  ",
    )

    isolation_observer.observe(unnormalized_event)

    normalized_observation = isolation_observer.get(
        "execution-unnormalized"
    )

    if normalized_observation is None:
        raise RuntimeError(
            "Observation stored under an unnormalized "
            "execution_id must still be queryable via the "
            "normalized ID."
        )

    if isolation_observer.count() != 1:
        raise RuntimeError(
            "Expected exactly one observation, not a "
            "duplicate/orphaned entry."
        )

    # A malformed (non-string) execution_id on an event must
    # be silently ignored, not crash observe()/the event bus.
    try:
        isolation_observer.observe(
            ExecutionEvent(
                event_type=ExecutionEventType.STARTED,
                execution_id=None,
            )
        )
    except Exception as exc:
        raise RuntimeError(
            "observe() raised for a non-string event "
            f"execution_id: {type(exc).__name__}: {exc}"
        )

    if isolation_observer.count() != 1:
        raise RuntimeError(
            "A malformed execution_id must not create an "
            "observation entry."
        )

    isolation_observer.close()

    print("UNNORMALIZED EXECUTION ID KEY CONSISTENCY: PASS")

    print()
    print("=" * 60)
    print("EXECUTION OBSERVER: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()