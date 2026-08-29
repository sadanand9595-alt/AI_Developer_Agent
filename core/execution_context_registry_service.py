"""
Application-facing service for the execution context registry.

Provides a controlled API for registering, resolving, and
removing ExecutionContext instances.
"""

from __future__ import annotations

from core.execution_context import ExecutionContext
from core.execution_context_registry import (
    ExecutionContextRegistry,
)


class ExecutionContextRegistryService:
    """Service boundary over ExecutionContextRegistry."""

    def __init__(
        self,
        registry: ExecutionContextRegistry,
    ) -> None:
        if not isinstance(
            registry,
            ExecutionContextRegistry,
        ):
            raise TypeError(
                "Expected an ExecutionContextRegistry instance."
            )

        self._registry = registry

    def register(
        self,
        context: ExecutionContext,
    ) -> None:
        """Register an execution context."""

        self._registry.register(
            context
        )

    def unregister(
        self,
        context_id: str,
    ) -> bool:
        """Unregister a context by context ID."""

        return self._registry.unregister(
            context_id
        )

    def get(
        self,
        context_id: str,
    ) -> ExecutionContext | None:
        """Get a context by context ID."""

        return self._registry.get(
            context_id
        )

    def get_by_execution(
        self,
        execution_id: str,
    ) -> ExecutionContext | None:
        """Get a context by execution ID."""

        return self._registry.get_by_execution(
            execution_id
        )

    def contains(
        self,
        context_id: str,
    ) -> bool:
        """Check whether a context is registered."""

        return self._registry.contains(
            context_id
        )

    def count(self) -> int:
        """Return the number of registered contexts."""

        return self._registry.count()

    def ids(self) -> tuple[str, ...]:
        """Return all registered context IDs."""

        return self._registry.ids()

    def all(
        self,
    ) -> tuple[ExecutionContext, ...]:
        """Return all registered contexts."""

        return self._registry.all()

    def clear(self) -> int:
        """Clear all registered contexts."""

        return self._registry.clear()


__all__ = [
    "ExecutionContextRegistryService",
]