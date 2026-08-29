"""
Central registry for execution contexts.

Provides thread-safe registration, lookup, removal,
and lifecycle management for ExecutionContext instances.
"""

from __future__ import annotations

from threading import RLock

from core.execution_context import ExecutionContext


class ExecutionContextRegistry:
    """Thread-safe registry for execution contexts."""

    def __init__(self) -> None:
        self._contexts: dict[str, ExecutionContext] = {}
        self._lock = RLock()

    def register(
        self,
        context: ExecutionContext,
    ) -> None:
        """Register an execution context."""

        if not isinstance(
            context,
            ExecutionContext,
        ):
            raise TypeError(
                "Expected an ExecutionContext instance."
            )

        with self._lock:
            if context.context_id in self._contexts:
                raise ValueError(
                    (
                        "Context is already registered: "
                        f"{context.context_id}"
                    )
                )

            self._contexts[
                context.context_id
            ] = context

    def unregister(
        self,
        context_id: str,
    ) -> bool:
        """Remove a context by context ID."""

        normalized_id = context_id.strip()

        if not normalized_id:
            return False

        with self._lock:
            return (
                self._contexts.pop(
                    normalized_id,
                    None,
                )
                is not None
            )

    def get(
        self,
        context_id: str,
    ) -> ExecutionContext | None:
        """Get a context by context ID."""

        normalized_id = context_id.strip()

        if not normalized_id:
            return None

        with self._lock:
            return self._contexts.get(
                normalized_id
            )

    def get_by_execution(
        self,
        execution_id: str,
    ) -> ExecutionContext | None:
        """Get a context by execution ID."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return None

        with self._lock:
            for context in self._contexts.values():
                if context.execution_id == normalized_id:
                    return context

        return None

    def contains(
        self,
        context_id: str,
    ) -> bool:
        """Return whether a context is registered."""

        return self.get(context_id) is not None

    def count(self) -> int:
        """Return the number of registered contexts."""

        with self._lock:
            return len(
                self._contexts
            )

    def ids(self) -> tuple[str, ...]:
        """Return all registered context IDs."""

        with self._lock:
            return tuple(
                self._contexts.keys()
            )

    def all(
        self,
    ) -> tuple[ExecutionContext, ...]:
        """Return all registered contexts."""

        with self._lock:
            return tuple(
                self._contexts.values()
            )

    def clear(self) -> int:
        """Remove all registered contexts."""

        with self._lock:
            count = len(
                self._contexts
            )

            self._contexts.clear()

            return count


__all__ = [
    "ExecutionContextRegistry",
]