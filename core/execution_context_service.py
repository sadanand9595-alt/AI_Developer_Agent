"""
Application-facing service for execution contexts.

Provides controlled creation, registration, lookup, removal,
and lifecycle management for ExecutionContext instances.
"""

from __future__ import annotations

from threading import RLock

from core.execution_context import ExecutionContext


class ExecutionContextService:
    """Thread-safe service for managing execution contexts."""

    def __init__(self) -> None:
        self._contexts: dict[str, ExecutionContext] = {}
        self._lock = RLock()

    def create(
        self,
        *,
        execution_id: str,
        user_id: str | None = None,
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
        """Create and register a new execution context."""

        context = ExecutionContext.create(
            execution_id=execution_id,
            user_id=user_id,
            task_id=task_id,
            session_id=session_id,
            agent_id=agent_id,
            workspace_root=workspace_root,
            working_directory=working_directory,
            permissions=permissions,
            metadata=metadata,
        )

        with self._lock:
            if context.context_id in self._contexts:
                raise RuntimeError(
                    (
                        "Context ID collision: "
                        f"{context.context_id}"
                    )
                )

            self._contexts[
                context.context_id
            ] = context

        return context

    def register(
        self,
        context: ExecutionContext,
    ) -> None:
        """Register an existing execution context."""

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

    def get(
        self,
        context_id: str,
    ) -> ExecutionContext | None:
        """Return a context by context ID."""

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
        """Return the context associated with an execution."""

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

    def remove_by_execution(
        self,
        execution_id: str,
    ) -> bool:
        """Remove the context associated with an execution."""

        context = self.get_by_execution(
            execution_id
        )

        if context is None:
            return False

        return self.unregister(
            context.context_id
        )

    def count(self) -> int:
        """Return the number of registered contexts."""

        with self._lock:
            return len(
                self._contexts
            )

    def all(self) -> tuple[ExecutionContext, ...]:
        """Return all registered contexts."""

        with self._lock:
            return tuple(
                self._contexts.values()
            )

    def clear(self) -> int:
        """Remove all contexts."""

        with self._lock:
            count = len(
                self._contexts
            )

            self._contexts.clear()

            return count


__all__ = [
    "ExecutionContextService",
]
