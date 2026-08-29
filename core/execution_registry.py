"""
Central execution registry for AI Command Center.

Maintains a thread-safe registry of active execution
instances and provides controlled lookup operations.
"""

from __future__ import annotations

from threading import RLock
from typing import Any


class ExecutionRegistry:
    """Thread-safe registry for execution instances."""

    def __init__(self) -> None:
        self._executions: dict[str, Any] = {}
        self._lock = RLock()

    def register(
        self,
        execution_id: str,
        execution: Any,
    ) -> None:
        """Register an execution instance."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        if execution is None:
            raise ValueError(
                "Execution instance cannot be None."
            )

        with self._lock:
            if normalized_id in self._executions:
                raise ValueError(
                    (
                        "Execution is already registered: "
                        f"{normalized_id}"
                    )
                )

            self._executions[
                normalized_id
            ] = execution

    def unregister(
        self,
        execution_id: str,
    ) -> bool:
        """Remove an execution from the registry."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return False

        with self._lock:
            return (
                self._executions.pop(
                    normalized_id,
                    None,
                )
                is not None
            )

    def get(
        self,
        execution_id: str,
    ) -> Any | None:
        """Return a registered execution."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return None

        with self._lock:
            return self._executions.get(
                normalized_id
            )

    def contains(
        self,
        execution_id: str,
    ) -> bool:
        """Return whether an execution is registered."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return False

        with self._lock:
            return normalized_id in self._executions

    def count(self) -> int:
        """Return the number of registered executions."""

        with self._lock:
            return len(
                self._executions
            )

    def ids(self) -> tuple[str, ...]:
        """Return all registered execution IDs."""

        with self._lock:
            return tuple(
                self._executions.keys()
            )

    def all(
        self,
    ) -> tuple[Any, ...]:
        """Return all registered execution instances."""

        with self._lock:
            return tuple(
                self._executions.values()
            )

    def clear(self) -> int:
        """Remove all registered executions."""

        with self._lock:
            count = len(
                self._executions
            )

            self._executions.clear()

            return count