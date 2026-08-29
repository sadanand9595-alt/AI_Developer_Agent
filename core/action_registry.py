"""
Action registry for AI Command Center.

Maps validated execution-plan actions to callable handlers.
"""

from __future__ import annotations

from threading import RLock
from typing import Any, Callable

from core.result import Result


ActionHandler = Callable[..., Result[Any]]


class ActionRegistry:
    """Thread-safe registry of executable actions."""

    def __init__(self) -> None:
        self._actions: dict[str, ActionHandler] = {}
        self._lock = RLock()

    def register(
        self,
        name: str,
        handler: ActionHandler,
        *,
        replace: bool = False,
    ) -> Result[None]:
        """Register an action handler."""

        normalized_name = name.strip()

        if not normalized_name:
            return Result.fail(
                "INVALID_ACTION_NAME",
                "Action name cannot be empty.",
            )

        if not callable(handler):
            return Result.fail(
                "INVALID_ACTION_HANDLER",
                "Action handler must be callable.",
            )

        with self._lock:
            if (
                normalized_name in self._actions
                and not replace
            ):
                return Result.fail(
                    "ACTION_ALREADY_REGISTERED",
                    "Action is already registered.",
                    details={
                        "action": normalized_name,
                    },
                )

            self._actions[
                normalized_name
            ] = handler

        return Result.ok()

    def unregister(
        self,
        name: str,
    ) -> Result[None]:
        """Remove an action handler."""

        normalized_name = name.strip()

        if not normalized_name:
            return Result.fail(
                "INVALID_ACTION_NAME",
                "Action name cannot be empty.",
            )

        with self._lock:
            if normalized_name not in self._actions:
                return Result.fail(
                    "ACTION_NOT_FOUND",
                    "Action is not registered.",
                    details={
                        "action": normalized_name,
                    },
                )

            del self._actions[
                normalized_name
            ]

        return Result.ok()

    def get(
        self,
        name: str,
    ) -> Result[ActionHandler]:
        """Return a registered action handler."""

        normalized_name = name.strip()

        if not normalized_name:
            return Result.fail(
                "INVALID_ACTION_NAME",
                "Action name cannot be empty.",
            )

        with self._lock:
            handler = self._actions.get(
                normalized_name
            )

            if handler is None:
                return Result.fail(
                    "ACTION_NOT_FOUND",
                    "Action is not registered.",
                    details={
                        "action": normalized_name,
                    },
                )

            return Result.ok(handler)

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether an action is registered."""

        normalized_name = name.strip()

        if not normalized_name:
            return False

        with self._lock:
            return normalized_name in self._actions

    def list_actions(self) -> tuple[str, ...]:
        """Return registered action names."""

        with self._lock:
            return tuple(
                sorted(self._actions)
            )

    def count(self) -> int:
        """Return the number of registered actions."""

        with self._lock:
            return len(self._actions)

    def clear(self) -> None:
        """Remove all registered actions."""

        with self._lock:
            self._actions.clear()