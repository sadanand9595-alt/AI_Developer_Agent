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

    if wildcard_received != [
        ExecutionEventType.STARTED,
        ExecutionEventType.COMPLETED,
    ]:
        raise RuntimeError(
            "Wildcard listener should receive completed event."
        )

    if received != [
        ExecutionEventType.STARTED
    ]:
        raise RuntimeError(
            "Specific listener should not receive completed event."
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
    ) != 2:
        raise RuntimeError(
            "Duplicate listener registration should be counted."
        )

    print("DUPLICATE SUBSCRIBE: PASS")

    # -------------------------------------------------
    # UNSUBSCRIBE ONE REGISTRATION
    # -------------------------------------------------

    removed = bus.unsubscribe(
        started_listener,
        event_type=ExecutionEventType.STARTED,
    )

    if not removed:
        raise RuntimeError(
            "Listener registration should be removed."
        )

    if bus.listener_count(
        ExecutionEventType.STARTED
    ) != 1:
        raise RuntimeError(
            "Exactly one specific listener registration should remain."
        )

    print("UNSUBSCRIBE: PASS")

    # -------------------------------------------------
    # PUBLISH AFTER ONE UNSUBSCRIBE
    # -------------------------------------------------

    received.clear()
    wildcard_received.clear()

    notified = bus.publish(
        ExecutionEvent.create(
            event_type=ExecutionEventType.STARTED,
            execution_id="execution-002",
        )
    )

    if notified != 2:
        raise RuntimeError(
            "Remaining specific and wildcard listeners should be notified."
        )

    if received != [
        ExecutionEventType.STARTED
    ]:
        raise RuntimeError(
            "Remaining specific listener should receive the event."
        )

    if wildcard_received != [
        ExecutionEventType.STARTED
    ]:
        raise RuntimeError(
            "Wildcard listener should still receive the event."
        )

    print("POST-UNSUBSCRIBE PUBLISH: PASS")

    # -------------------------------------------------
    # LISTENER EXCEPTION ISOLATION
    # -------------------------------------------------

    isolation_bus = ExecutionEventBus()
    isolation_received: list[str] = []

    def failing_listener(event: ExecutionEvent) -> None:
        raise RuntimeError("boom")

    def surviving_listener(event: ExecutionEvent) -> None:
        isolation_received.append(event.event_type)

    isolation_bus.subscribe(failing_listener)
    isolation_bus.subscribe(surviving_listener)

    import logging

    class _CapturingHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.records: list[logging.LogRecord] = []

        def emit(self, record: logging.LogRecord) -> None:
            self.records.append(record)

    capture_handler = _CapturingHandler()
    bus_logger = logging.getLogger("core.execution_event_bus")
    bus_logger.addHandler(capture_handler)
    previous_level = bus_logger.level
    bus_logger.setLevel(logging.ERROR)

    try:
        isolation_notified = isolation_bus.publish(
            ExecutionEvent.create(
                event_type=ExecutionEventType.STARTED,
                execution_id="execution-003",
            )
        )
    finally:
        bus_logger.removeHandler(capture_handler)
        bus_logger.setLevel(previous_level)

    if isolation_notified != 2:
        raise RuntimeError(
            "Both listeners should be attempted despite one raising."
        )

    if isolation_received != [ExecutionEventType.STARTED]:
        raise RuntimeError(
            "Surviving listener should still receive the event."
        )

    if not capture_handler.records:
        raise RuntimeError(
            "Listener failure should be logged."
        )

    print("LISTENER EXCEPTION ISOLATION: PASS")

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

    if ExecutionEventType.STARTED not in event_types:
        raise RuntimeError(
            "Started event subscription should still exist."
        )

    print("EVENT TYPE LISTING: PASS")

    # -------------------------------------------------
    # CLEAR SPECIFIC TYPE
    # -------------------------------------------------

    bus.clear(
        ExecutionEventType.STARTED,
    )

    if bus.listener_count(
        ExecutionEventType.STARTED
    ) != 0:
        raise RuntimeError(
            "Started listeners should be cleared."
        )

    if bus.listener_count() != 1:
        raise RuntimeError(
            "Wildcard listener should remain after specific clear."
        )

    print("CLEAR SPECIFIC: PASS")

    # -------------------------------------------------
    # CLEAR ALL
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

    # Non-string event_type must not crash.
    try:
        bus.subscribe(lambda e: None, event_type=123)
    except TypeError:
        pass
    else:
        raise RuntimeError(
            "Non-string event_type should be rejected."
        )

    if bus.unsubscribe(lambda e: None, event_type=123):
        raise RuntimeError(
            "Non-string event_type unsubscribe should be a no-op."
        )

    if bus.listener_count(event_type=123) != 0:
        raise RuntimeError(
            "Non-string event_type listener_count should be 0."
        )

    bus.clear(event_type=123)

    print("NON-STRING EVENT TYPE SAFETY: PASS")

    print()
    print("=" * 60)
    print("EXECUTION EVENT BUS: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()