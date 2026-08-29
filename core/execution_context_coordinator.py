"""
Execution context coordinator for AI Command Center.

Coordinates context creation, registration, lookup, updates,
and cleanup behind a single application-facing boundary.

Design notes
------------
The underlying ExecutionContext is immutable by design.

Normal ExecutionContextCoordinator instances therefore use
immutable update semantics:

    original = coordinator.create(...)
    updated = coordinator.update_agent(...)

    original is not updated

ExecutionContextCoordinatorFactory may explicitly enable
identity-preserving compatibility mode for legacy callers that
expect update methods to return the original object.
"""

from __future__ import annotations

from core.execution_context import ExecutionContext
from core.execution_context_service import (
    ExecutionContextService,
)
from core.execution_context_registry import (
    ExecutionContextRegistry,
)
from core.execution_context_registry_service import (
    ExecutionContextRegistryService,
)


class ExecutionContextCoordinator:
    """Coordinates execution context lifecycle."""

    def __init__(
        self,
        context_service: ExecutionContextService | None = None,
        registry_service: (
            ExecutionContextRegistryService | None
        ) = None,
        *,
        preserve_identity_on_update: bool = False,
    ) -> None:
        """
        Create an ExecutionContextCoordinator.

        Parameters
        ----------
        context_service:
            Optional execution context service.

        registry_service:
            Optional registry service.

        preserve_identity_on_update:
            When False, updates create a new ExecutionContext
            and preserve the immutable-context contract.

            When True, updates modify the existing context object
            in-place and return that same object.

            This compatibility mode exists specifically for
            legacy factory consumers whose tests/contracts expect:

                updated is original
        """

        self._context_service = (
            context_service
            if context_service is not None
            else ExecutionContextService()
        )

        self._registry_service = (
            registry_service
            if registry_service is not None
            else ExecutionContextRegistryService(
                ExecutionContextRegistry()
            )
        )

        self._preserve_identity_on_update = (
            preserve_identity_on_update
        )

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    def create(
        self,
        execution_id: str,
        *,
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
        """
        Create and register an execution context.

        execution_id may be supplied positionally or by keyword.
        """

        context = self._context_service.create(
            execution_id=execution_id,
            task_id=task_id,
            session_id=session_id,
            agent_id=agent_id,
            workspace_root=workspace_root,
            working_directory=working_directory,
            permissions=permissions,
            metadata=metadata,
        )

        try:
            self._registry_service.register(
                context
            )

        except Exception:
            self._context_service.unregister(
                context.context_id
            )
            raise

        return context

    # -------------------------------------------------
    # REGISTER
    # -------------------------------------------------

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

        # Register in the context service first when needed.
        existing_service_context = (
            self._context_service.get(
                context.context_id
            )
        )

        if existing_service_context is None:
            self._context_service.register(
                context
            )

        # Register in the central registry when needed.
        existing_registry_context = (
            self._registry_service.get(
                context.context_id
            )
        )

        if existing_registry_context is None:
            try:
                self._registry_service.register(
                    context
                )

            except Exception:
                # Roll back a service registration that was created
                # by this method.
                if (
                    existing_service_context is None
                    and self._context_service.get(
                        context.context_id
                    )
                    is context
                ):
                    self._context_service.unregister(
                        context.context_id
                    )

                raise

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    def get(
        self,
        context_id: str,
    ) -> ExecutionContext | None:
        """
        Get a context.

        Supports both:

        - context_id
        - execution_id
        """

        context = self._registry_service.get(
            context_id
        )

        if context is not None:
            return context

        return self._registry_service.get_by_execution(
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

        return self._registry_service.get_by_execution(
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

        return self.get(
            context_id
        ) is not None

    # -------------------------------------------------
    # IDS
    # -------------------------------------------------

    def ids(
        self,
    ) -> tuple[str, ...]:
        """Return all active context IDs."""

        return tuple(
            context.context_id
            for context in self.all()
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

        Both forms are supported:

            update_metadata(
                "context-id",
                {"mode": "test"},
            )

        and:

            update_metadata(
                "context-id",
                mode="test",
            )

        Default behavior:
            Returns a new ExecutionContext and leaves the original
            object unchanged.

        Compatibility behavior:
            When preserve_identity_on_update=True, updates the
            existing object and returns the same object.
        """

        context = self.get(
            context_id
        )

        if context is None:
            raise KeyError(
                f"Context not found: {context_id}"
            )

        merged_updates: dict[str, object] = {}

        if metadata is not None:
            merged_updates.update(
                metadata
            )

        merged_updates.update(
            updates
        )

        # -------------------------------------------------
        # LEGACY / FACTORY IDENTITY MODE
        # -------------------------------------------------

        if self._preserve_identity_on_update:
            context.metadata.update(
                merged_updates
            )

            return context

        # -------------------------------------------------
        # IMMUTABLE MODE
        # -------------------------------------------------

        updated = context.with_metadata(
            **merged_updates
        )

        self._replace(
            context,
            updated,
        )

        return updated

    # -------------------------------------------------
    # UPDATE WORKING DIRECTORY
    # -------------------------------------------------

    def update_working_directory(
        self,
        context_id: str,
        working_directory: str,
    ) -> ExecutionContext:
        """
        Update the working directory.

        Normal coordinators return a new context.

        Factory compatibility mode preserves the original
        object identity.
        """

        context = self.get(
            context_id
        )

        if context is None:
            raise KeyError(
                f"Context not found: {context_id}"
            )

        # -------------------------------------------------
        # LEGACY / FACTORY IDENTITY MODE
        # -------------------------------------------------

        if self._preserve_identity_on_update:
            object.__setattr__(
                context,
                "working_directory",
                working_directory,
            )

            return context

        # -------------------------------------------------
        # IMMUTABLE MODE
        # -------------------------------------------------

        updated = context.with_working_directory(
            working_directory
        )

        self._replace(
            context,
            updated,
        )

        return updated

    # -------------------------------------------------
    # UPDATE AGENT
    # -------------------------------------------------

    def update_agent(
        self,
        context_id: str,
        agent_id: str,
    ) -> ExecutionContext:
        """
        Update the agent associated with a context.

        Normal coordinators return a new context.

        Factory compatibility mode preserves the original
        object identity.
        """

        context = self.get(
            context_id
        )

        if context is None:
            raise KeyError(
                f"Context not found: {context_id}"
            )

        # -------------------------------------------------
        # LEGACY / FACTORY IDENTITY MODE
        # -------------------------------------------------

        if self._preserve_identity_on_update:
            object.__setattr__(
                context,
                "agent_id",
                agent_id,
            )

            return context

        # -------------------------------------------------
        # IMMUTABLE MODE
        # -------------------------------------------------

        updated = context.with_agent(
            agent_id
        )

        self._replace(
            context,
            updated,
        )

        return updated

    # -------------------------------------------------
    # UNREGISTER
    # -------------------------------------------------

    def unregister(
        self,
        context_id: str,
    ) -> bool:
        """
        Unregister and remove a context.

        Accepts either context ID or execution ID.
        """

        context = self.get(
            context_id
        )

        if context is not None:
            target_id = context.context_id
        else:
            target_id = context_id

        registry_removed = (
            self._registry_service.unregister(
                target_id
            )
        )

        service_removed = (
            self._context_service.unregister(
                target_id
            )
        )

        return (
            registry_removed
            or service_removed
        )

    # -------------------------------------------------
    # REMOVE
    # -------------------------------------------------

    def remove(
        self,
        context_id: str,
    ) -> bool:
        """Remove a context by context ID or execution ID."""

        return self.unregister(
            context_id
        )

    # -------------------------------------------------
    # REMOVE BY EXECUTION
    # -------------------------------------------------

    def remove_by_execution(
        self,
        execution_id: str,
    ) -> bool:
        """Remove a context associated with an execution."""

        context = self.get_by_execution(
            execution_id
        )

        if context is None:
            return False

        return self.unregister(
            context.context_id
        )

    # -------------------------------------------------
    # COUNT
    # -------------------------------------------------

    def count(
        self,
    ) -> int:
        """Return the number of active contexts."""

        return self._registry_service.count()

    # -------------------------------------------------
    # ALL
    # -------------------------------------------------

    def all(
        self,
    ) -> tuple[ExecutionContext, ...]:
        """Return all active contexts."""

        return self._registry_service.all()

    # -------------------------------------------------
    # CLEAR
    # -------------------------------------------------

    def clear(
        self,
    ) -> int:
        """Clear all contexts from both stores."""

        registry_count = (
            self._registry_service.clear()
        )

        self._context_service.clear()

        return registry_count

    # -------------------------------------------------
    # INTERNAL REPLACE
    # -------------------------------------------------

    def _replace(
        self,
        original: ExecutionContext,
        updated: ExecutionContext,
    ) -> None:
        """
        Replace a context atomically across both stores.

        This method is used only by immutable update operations.
        """

        self._registry_service.unregister(
            original.context_id
        )

        self._context_service.unregister(
            original.context_id
        )

        try:
            self._context_service.register(
                updated
            )

            self._registry_service.register(
                updated
            )

        except Exception:

            self._context_service.unregister(
                updated.context_id
            )

            self._registry_service.unregister(
                updated.context_id
            )

            self._context_service.register(
                original
            )

            self._registry_service.register(
                original
            )

            raise


__all__ = [
    "ExecutionContextCoordinator",
]