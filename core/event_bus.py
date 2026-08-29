"""
In-process event bus for AI Command Center.

The event bus provides lightweight publish/subscribe communication
between independent application components.
"""

from __future__ import annotations

import asyncio
import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from core.events import Event, EventType


EventHandler = Callable[[Event], Any]
AsyncEventHandler = Callable[[Event], Awaitable[Any]]


class EventBus:
    """
    Publish/subscribe event dispatcher.

    Handlers can be synchronous or asynchronous.
    """

    def __init__(self) -> None:
        self._handlers: dict[
            EventType,
            list[EventHandler | AsyncEventHandler],
        ] = defaultdict(list)

    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler | AsyncEventHandler,
    ) -> None:
        """
        Register a handler for an event type.

        Duplicate registrations of the same handler are ignored.
        """

        handlers = self._handlers[event_type]

        if handler not in handlers:
            handlers.append(handler)

    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler | AsyncEventHandler,
    ) -> None:
        """Remove a previously registered event handler."""

        handlers = self._handlers.get(event_type)

        if not handlers:
            return

        if handler in handlers:
            handlers.remove(handler)

        if not handlers:
            self._handlers.pop(event_type, None)

    def clear(self) -> None:
        """Remove all registered handlers."""

        self._handlers.clear()

    def handler_count(self, event_type: EventType) -> int:
        """Return the number of handlers registered for an event."""

        return len(self._handlers.get(event_type, []))

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all registered handlers.

        Handlers are executed independently. A handler failure is
        allowed to propagate so callers can decide how failures
        should be handled.
        """

        handlers = list(
            self._handlers.get(event.event_type, [])
        )

        if not handlers:
            return

        for handler in handlers:
            result = handler(event)

            if inspect.isawaitable(result):
                await result

    async def publish_parallel(self, event: Event) -> None:
        """
        Publish an event to all handlers concurrently.

        This is useful for independent observers such as logging,
        metrics, and monitoring.
        """

        handlers = list(
            self._handlers.get(event.event_type, [])
        )

        if not handlers:
            return

        awaitables: list[Awaitable[Any]] = []

        for handler in handlers:
            result = handler(event)

            if inspect.isawaitable(result):
                awaitables.append(result)
            else:
                # Synchronous handlers are already completed.
                continue

        if awaitables:
            await asyncio.gather(*awaitables)

    def get_handlers(
        self,
        event_type: EventType,
    ) -> tuple[EventHandler | AsyncEventHandler, ...]:
        """Return registered handlers without exposing internal state."""

        return tuple(
            self._handlers.get(event_type, [])
        )