from core.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)
from core.execution_event_bus import ExecutionEventBus


def main() -> None:
    bus = ExecutionEventBus()

    received: list[str] = []
    wildcard_received: list[str] = []

    def started_listener(event: ExecutionEvent) -> None:
        received.append(event.event_type)

    def wildcard_listener(event: ExecutionEvent) -> None:
        wildcard_received.append(event.event_type)

    # -------------------------------------------------
    # SUBSCRIBE
    # -------------------------------------------------

    bus.subscribe(
        started_listener,
        event_type=ExecutionEventType.STARTED,
    )

    bus.subscribe(
        wildcard_listener,
    )

    if bus.listener_count(
        ExecutionEventType.STARTED
    ) != 1:
        raise RuntimeError(
            "Started listener should be registered."
        )

    if bus.listener_count() != 1:
        raise RuntimeError(
            "Wildcard listener should be registered."
        )

    print("SUBSCRIBE: PASS")

    # -------------------------------------------------
    # PUBLISH STARTED EVENT
    # -------------------------------------------------

    started = ExecutionEvent.create(
        event_type=ExecutionEventType.STARTED,
        execution_id="execution-001",
        task_id="task-001",
    )

    notified = bus.publish(started)

    print(
        "NOTIFIED STARTED:",
        notified,
    )

    if notified != 2:
        raise RuntimeError(
            "Both specific and wildcard listeners should be notified."
        )

    if received != [
        ExecutionEventType.STARTED
    ]:
        raise RuntimeError(
            "Specific listener received incorrect event."
        )

    if wildcard_received != [
        ExecutionEventType.STARTED
    ]:
        raise RuntimeError(
            "Wildcard listener received incorrect event."
        )

    print("PUBLISH SPECIFIC: PASS")
    print("PUBLISH WILDCARD: PASS")

    # -------------------------------------------------
    # PUBLISH NON-MATCHING EVENT
    # -------------------------------------------------

    completed = ExecutionEvent.create(
        event_type=ExecutionEventType.COMPLETED,
        execution_id="execution-001",
        task_id="task-001",
    )

    notified = bus.publish(completed)

    if notified != 1:
        raise RuntimeError(
            "Only wildcard listener should receive completed event."
        )

    print("EVENT FILTERING: PASS")

    # -------------------------------------------------
    # DUPLICATE SUBSCRIBE
    # -------------------------------------------------

    bus.subscribe(
        started_listener,
        event_type=ExecutionEventType.STARTED,
    )

    if bus.listener_count(
        ExecutionEventType.STARTED
    ) != 1:
        raise RuntimeError(
            "Duplicate listener should not be added."
        )

    print("DUPLICATE SUBSCRIBE PROTECTION: PASS")

    # -------------------------------------------------
    # UNSUBSCRIBE
    # -------------------------------------------------

    removed = bus.unsubscribe(
        started_listener,
        event_type=ExecutionEventType.STARTED,
    )

    if not removed:
        raise RuntimeError(
            "Listener should be removed."
        )

    if bus.listener_count(
        ExecutionEventType.STARTED
    ) != 0:
        raise RuntimeError(
            "Listener should no longer exist."
        )

    print("UNSUBSCRIBE: PASS")

    # -------------------------------------------------
    # PUBLISH AFTER UNSUBSCRIBE
    # -------------------------------------------------

    received.clear()
    wildcard_received.clear()

    notified = bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STARTED,
            execution_id="execution-002",
        )
    )

    if notified != 1:
        raise RuntimeError(
            "Only wildcard listener should remain."
        )

    if received:
        raise RuntimeError(
            "Unsubscribed listener received an event."
        )

    if wildcard_received != [
        ExecutionEventType.STARTED
    ]:
        raise RuntimeError(
            "Wildcard listener should still receive events."
        )

    print("POST-UNSUBSCRIBE PUBLISH: PASS")

    # -------------------------------------------------
    # INVALID EVENT
    # -------------------------------------------------

    try:
        bus.publish("invalid-event")
    except TypeError:
        print("INVALID EVENT: PASS")
    else:
        raise RuntimeError(
            "Invalid event should be rejected."
        )

    # -------------------------------------------------
    # INVALID LISTENER
    # -------------------------------------------------

    try:
        bus.subscribe(
            "invalid-listener",
        )
    except TypeError:
        print("INVALID LISTENER: PASS")
    else:
        raise RuntimeError(
            "Invalid listener should be rejected."
        )

    # -------------------------------------------------
    # EVENT TYPES
    # -------------------------------------------------

    event_types = bus.event_types()

    print(
        "EVENT TYPES:",
        event_types,
    )

    if "*" not in event_types:
        raise RuntimeError(
            "Wildcard subscription should exist."
        )

    print("EVENT TYPE LISTING: PASS")

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    bus.clear()

    if bus.listener_count() != 0:
        raise RuntimeError(
            "All listeners should be cleared."
        )

    if bus.event_types():
        raise RuntimeError(
            "Event types should be empty after clear."
        )

    print("CLEAR: PASS")

    print()
    print("=" * 60)
    print("EXECUTION EVENT BUS: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()