"""
Application-facing execution context API.

Provides a stable boundary between the application layer
and the internal execution-context coordination subsystem.

The application layer uses the normal immutable
ExecutionContextCoordinator behavior. Factory-specific
legacy identity-preserving behavior is intentionally not used
for the default application instance.
"""

from __future__ import annotations

from core.execution_context import ExecutionContext
from core.execution_context_coordinator import (
    ExecutionContextCoordinator,
)


class ExecutionContextApplication:
    """Application-facing owner of execution contexts."""

    def __init__(
        self,
        coordinator: ExecutionContextCoordinator | None = None,
    ) -> None:
        """
        Create an execution context application.

        When no coordinator is supplied, a normal
        ExecutionContextCoordinator is created.

        This is intentional: the application layer must preserve
        ExecutionContext immutability during updates.

        A supplied coordinator is respected exactly as provided,
        which keeps dependency injection and testing supported.
        """

        if coordinator is not None and not isinstance(
            coordinator,
            ExecutionContextCoordinator,
        ):
            raise TypeError(
                "Expected an ExecutionContextCoordinator instance."
            )

        self._coordinator = (
            coordinator
            if coordinator is not None
            else ExecutionContextCoordinator()
        )

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    def create(
        self,
        *,
        execution_id: str,
        task_id: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
        workspace_root: str = ".",
        working_directory: str = ".",
        permissions: set[str]
        | frozenset[str]
        | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionContext:
        """Create and register an execution context."""

        return self._coordinator.create(
            execution_id=execution_id,
            task_id=task_id,
            session_id=session_id,
            agent_id=agent_id,
            workspace_root=workspace_root,
            working_directory=working_directory,
            permissions=permissions,
            metadata=metadata,
        )

    # -------------------------------------------------
    # REGISTER
    # -------------------------------------------------

    def register(
        self,
        context: ExecutionContext,
    ) -> None:
        """Register an existing execution context."""

        self._coordinator.register(
            context
        )

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    def get(
        self,
        context_id: str,
    ) -> ExecutionContext | None:
        """Get a context by context ID or execution ID."""

        return self._coordinator.get(
            context_id
        )

    # -------------------------------------------------
    # GET BY EXECUTION
    # -------------------------------------------------

    def get_by_execution(
        self,
        execution_id: str,
    ) -> ExecutionContext | None:
        """Get a context by execution ID."""

        return self._coordinator.get_by_execution(
            execution_id
        )

    # -------------------------------------------------
    # CONTAINS
    # -------------------------------------------------

    def contains(
        self,
        context_id: str,
    ) -> bool:
        """Return whether a context exists."""

        return self._coordinator.contains(
            context_id
        )

    # -------------------------------------------------
    # UPDATE METADATA
    # -------------------------------------------------

    def update_metadata(
        self,
        context_id: str,
        metadata: dict[str, object] | None = None,
        **updates: object,
    ) -> ExecutionContext:
        """
        Update context metadata.

        Normal application behavior preserves the immutable
        ExecutionContext contract by returning a new context
        object while leaving the original object unchanged.
        """

        return self._coordinator.update_metadata(
            context_id,
            metadata,
            **updates,
        )

    # -------------------------------------------------
    # UPDATE WORKING DIRECTORY
    # -------------------------------------------------

    def update_working_directory(
        self,
        context_id: str,
        working_directory: str,
    ) -> ExecutionContext:
        """
        Update the context working directory.

        The normal coordinator returns a new context and keeps
        the original context unchanged.
        """

        return self._coordinator.update_working_directory(
            context_id,
            working_directory,
        )

    # -------------------------------------------------
    # UPDATE AGENT
    # -------------------------------------------------

    def update_agent(
        self,
        context_id: str,
        agent_id: str,
    ) -> ExecutionContext:
        """
        Update the associated agent.

        The normal coordinator returns a new context and keeps
        the original context unchanged.
        """

        return self._coordinator.update_agent(
            context_id,
            agent_id,
        )

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    def unregister(
        self,
        context_id: str,
    ) -> bool:
        """Unregister a context by context ID or execution ID."""

        return self._coordinator.unregister(
            context_id
        )

    # -------------------------------------------------
    # REMOVE
    # -------------------------------------------------

    def remove(
        self,
        context_id: str,
    ) -> bool:
        """Remove a context by context ID or execution ID."""

        return self._coordinator.remove(
            context_id
        )

    # -------------------------------------------------
    # REMOVE BY EXECUTION
    # -------------------------------------------------

    def remove_by_execution(
        self,
        execution_id: str,
    ) -> bool:
        """Remove the context associated with an execution."""

        return self._coordinator.remove_by_execution(
            execution_id
        )

    # -------------------------------------------------
    # COUNT
    # -------------------------------------------------

    def count(
        self,
    ) -> int:
        """Return the number of active contexts."""

        return self._coordinator.count()

    # -------------------------------------------------
    # IDS
    # -------------------------------------------------

    def ids(
        self,
    ) -> tuple[str, ...]:
        """Return all active context IDs."""

        return self._coordinator.ids()

    # -------------------------------------------------
    # ALL
    # -------------------------------------------------

    def all(
        self,
    ) -> tuple[ExecutionContext, ...]:
        """Return all active contexts."""

        return self._coordinator.all()

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    def clear(
        self,
    ) -> int:
        """Clear all active contexts."""

        return self._coordinator.clear()


__all__ = [
    "ExecutionContextApplication",
]