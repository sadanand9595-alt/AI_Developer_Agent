"""
In-process event bus for AI Command Center.

Provides lightweight publish/subscribe communication between
independent application components.

Features:
- Synchronous and asynchronous handlers
- Duplicate subscription protection
- Thread-safe subscription management
- Snapshot-based publishing
- Sequential publishing
- Parallel publishing
- Exception isolation
- Safe unsubscribe and clear operations
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from threading import RLock
from typing import Any

from core.events import Event, EventType


logger = logging.getLogger(__name__)


Handler = Callable[[Event], Any | Awaitable[Any]]


class EventBus:
    """
    Thread-safe in-process event bus.

    Handlers may be synchronous or asynchronous.

    The bus protects subscription state with an RLock and always
    publishes from a snapshot of the current handlers so that
    subscribe/unsubscribe operations during publishing do not
    mutate the active iteration.
    """

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[Handler]] = defaultdict(list)
        self._lock = RLock()

    # ------------------------------------------------------------------
    # SUBSCRIBE
    # ------------------------------------------------------------------

    def subscribe(
        self,
        event_type: EventType,
        handler: Handler,
    ) -> None:
        """
        Subscribe a handler to an event type.

        Duplicate subscriptions are ignored.
        """

        if not callable(handler):
            raise TypeError("handler must be callable.")

        with self._lock:
            handlers = self._handlers[event_type]

            if handler not in handlers:
                handlers.append(handler)

    # ------------------------------------------------------------------
    # UNSUBSCRIBE
    # ------------------------------------------------------------------

    def unsubscribe(
        self,
        event_type: EventType,
        handler: Handler,
    ) -> bool:
        """
        Remove a handler from an event type.

        Returns True if the handler was removed, otherwise False.
        """

        with self._lock:
            handlers = self._handlers.get(event_type)

            if not handlers:
                return False

            try:
                handlers.remove(handler)
            except ValueError:
                return False

            if not handlers:
                self._handlers.pop(event_type, None)

            return True

    # ------------------------------------------------------------------
    # CLEAR
    # ------------------------------------------------------------------

    def clear(
        self,
        event_type: EventType | None = None,
    ) -> None:
        """
        Clear subscriptions.

        If event_type is supplied, only handlers for that event type
        are removed.

        If event_type is None, all subscriptions are removed.
        """

        with self._lock:
            if event_type is None:
                self._handlers.clear()
                return

            self._handlers.pop(event_type, None)

    # ------------------------------------------------------------------
    # INSPECTION
    # ------------------------------------------------------------------

    def has_subscribers(
        self,
        event_type: EventType,
    ) -> bool:
        """Return True when an event type has at least one subscriber."""

        with self._lock:
            return bool(self._handlers.get(event_type))

    def subscriber_count(
        self,
        event_type: EventType,
    ) -> int:
        """Return the number of subscribers for an event type."""

        with self._lock:
            return len(self._handlers.get(event_type, ()))

    def registered_events(self) -> tuple[EventType, ...]:
        """Return all event types that currently have subscribers."""

        with self._lock:
            return tuple(
                event_type
                for event_type, handlers in self._handlers.items()
                if handlers
            )

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    def _snapshot_handlers(
        self,
        event_type: EventType,
    ) -> tuple[Handler, ...]:
        """
        Return an immutable snapshot of handlers for an event type.

        This prevents concurrent subscription changes from modifying
        the handler collection while an event is being published.
        """

        with self._lock:
            return tuple(self._handlers.get(event_type, ()))

    @staticmethod
    def _log_handler_error(
        handler: Handler,
        event: Event,
    ) -> None:
        """Log a handler failure without propagating it."""

        logger.exception(
            "Event handler failed: handler=%r event_type=%r",
            handler,
            getattr(event, "event_type", None),
        )

    # ------------------------------------------------------------------
    # PUBLISH
    # ------------------------------------------------------------------

    async def publish(
        self,
        event: Event,
    ) -> None:
        """
        Publish an event sequentially.

        Synchronous handlers execute immediately.

        Asynchronous handlers are awaited one at a time.

        Handler failures are isolated and logged. A failing handler
        does not prevent subsequent handlers from receiving the event.

        The event is intentionally not required to be an actual
        Event instance. The event bus operates on the event_type
        protocol used by the application's event objects and tests.
        """

        event_type = getattr(event, "event_type", None)

        if event_type is None:
            raise TypeError(
                "event must provide an event_type attribute."
            )

        handlers = self._snapshot_handlers(event_type)

        for handler in handlers:
            try:
                result = handler(event)

                if inspect.isawaitable(result):
                    await result

            except Exception:
                self._log_handler_error(handler, event)

    # ------------------------------------------------------------------
    # PUBLISH PARALLEL
    # ------------------------------------------------------------------

    async def publish_parallel(
        self,
        event: Event,
    ) -> None:
        """
        Publish an event to all handlers concurrently.

        Synchronous handlers are executed in worker threads.

        Asynchronous handlers are awaited concurrently.

        Handler failures are isolated and logged.

        All handlers are started from the same immutable snapshot.
        """

        event_type = getattr(event, "event_type", None)

        if event_type is None:
            raise TypeError(
                "event must provide an event_type attribute."
            )

        handlers = self._snapshot_handlers(event_type)

        if not handlers:
            return

        async def run_handler(handler: Handler) -> None:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                    return

                result = await asyncio.to_thread(
                    handler,
                    event,
                )

                if inspect.isawaitable(result):
                    await result

            except Exception:
                self._log_handler_error(handler, event)

        await asyncio.gather(
            *(run_handler(handler) for handler in handlers)
        )


# ----------------------------------------------------------------------
# GLOBAL EVENT BUS
# ----------------------------------------------------------------------

event_bus = EventBus()


# ----------------------------------------------------------------------
# CONVENIENCE HELPERS
# ----------------------------------------------------------------------

def subscribe(
    event_type: EventType,
    handler: Handler,
) -> None:
    """Subscribe a handler to the global event bus."""

    event_bus.subscribe(event_type, handler)


def unsubscribe(
    event_type: EventType,
    handler: Handler,
) -> bool:
    """Unsubscribe a handler from the global event bus."""

    return event_bus.unsubscribe(event_type, handler)


async def publish(
    event: Event,
) -> None:
    """Publish an event through the global event bus."""

    await event_bus.publish(event)


async def publish_parallel(
    event: Event,
) -> None:
    """Publish an event through the global event bus in parallel."""

    await event_bus.publish_parallel(event)


__all__ = [
    "EventBus",
    "Handler",
    "event_bus",
    "subscribe",
    "unsubscribe",
    "publish",
    "publish_parallel",
]
