"""
Application-facing execution registry service.

Provides a controlled service boundary over the execution
registry.
"""

from __future__ import annotations

from typing import Any

from core.execution_registry import ExecutionRegistry


class ExecutionRegistryService:
    """Service facade over ExecutionRegistry."""

    def __init__(
        self,
        registry: ExecutionRegistry,
    ) -> None:
        if not isinstance(
            registry,
            ExecutionRegistry,
        ):
            raise TypeError(
                "Expected an ExecutionRegistry instance."
            )

        self._registry = registry

    def register(
        self,
        execution_id: str,
        execution: Any,
    ) -> None:
        """Register an execution."""

        self._registry.register(
            execution_id,
            execution,
        )

    def unregister(
        self,
        execution_id: str,
    ) -> bool:
        """Unregister an execution."""

        return self._registry.unregister(
            execution_id
        )

    def get(
        self,
        execution_id: str,
    ) -> Any | None:
        """Get a registered execution."""

        return self._registry.get(
            execution_id
        )

    def contains(
        self,
        execution_id: str,
    ) -> bool:
        """Check whether an execution is registered."""

        return self._registry.contains(
            execution_id
        )

    def count(self) -> int:
        """Return the number of registered executions."""

        return self._registry.count()

    def ids(self) -> tuple[str, ...]:
        """Return registered execution IDs."""

        return self._registry.ids()

    def all(self) -> tuple[Any, ...]:
        """Return all registered executions."""

        return self._registry.all()

    def clear(self) -> int:
        """Clear all registered executions."""

        return self._registry.clear()