"""
Execution event bus for AI Command Center.

Provides thread-safe publish/subscribe behavior for execution
events.
"""

from __future__ import annotations

from threading import RLock
from typing import Callable

from core.execution_event import ExecutionEvent


EventListener = Callable[[ExecutionEvent], None]


class ExecutionEventBus:
    """Thread-safe event publisher for execution events."""

    def __init__(self) -> None:
        self._listeners: dict[
            str,
            list[EventListener],
        ] = {}

        self._lock = RLock()

    def subscribe(
        self,
        listener: EventListener,
        *,
        event_type: str | None = None,
    ) -> None:
        """Subscribe a listener to execution events."""

        if not callable(listener):
            raise TypeError(
                "Listener must be callable."
            )

        normalized_type = (
            event_type.strip()
            if event_type is not None
            else "*"
        )

        if not normalized_type:
            raise ValueError(
                "Event type cannot be empty."
            )

        with self._lock:
            listeners = self._listeners.setdefault(
                normalized_type,
                [],
            )

            if listener not in listeners:
                listeners.append(listener)

    def unsubscribe(
        self,
        listener: EventListener,
        *,
        event_type: str | None = None,
    ) -> bool:
        """Remove a listener from an event type."""

        normalized_type = (
            event_type.strip()
            if event_type is not None
            else "*"
        )

        if not normalized_type:
            return False

        with self._lock:
            listeners = self._listeners.get(
                normalized_type
            )

            if not listeners:
                return False

            if listener not in listeners:
                return False

            listeners.remove(listener)

            if not listeners:
                del self._listeners[
                    normalized_type
                ]

            return True

    def publish(
        self,
        event: ExecutionEvent,
    ) -> int:
        """
        Publish an event.

        Returns the number of listeners notified.
        """

        if not isinstance(
            event,
            ExecutionEvent,
        ):
            raise TypeError(
                "Expected an ExecutionEvent instance."
            )

        with self._lock:
            specific = list(
                self._listeners.get(
                    event.event_type,
                    [],
                )
            )

            wildcard = list(
                self._listeners.get(
                    "*",
                    [],
                )
            )

        notified = 0
        called: set[int] = set()

        for listener in (
            specific + wildcard
        ):
            listener_id = id(listener)

            if listener_id in called:
                continue

            called.add(listener_id)

            try:
                listener(event)
                notified += 1
            except Exception:
                continue

        return notified

    def listener_count(
        self,
        event_type: str | None = None,
    ) -> int:
        """Return the number of listeners for an event type."""

        normalized_type = (
            event_type.strip()
            if event_type is not None
            else "*"
        )

        if not normalized_type:
            return 0

        with self._lock:
            return len(
                self._listeners.get(
                    normalized_type,
                    [],
                )
            )

    def clear(
        self,
        event_type: str | None = None,
    ) -> None:
        """Remove listeners for one type or all listeners."""

        with self._lock:
            if event_type is None:
                self._listeners.clear()
                return

            normalized_type = event_type.strip()

            if normalized_type:
                self._listeners.pop(
                    normalized_type,
                    None,
                )

    def event_types(
        self,
    ) -> tuple[str, ...]:
        """Return registered event types."""

        with self._lock:
            return tuple(
                sorted(
                    self._listeners.keys()
                )
            )
