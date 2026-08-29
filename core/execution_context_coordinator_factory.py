"""
Factory for creating ExecutionContextCoordinator instances.

Provides a simple application-facing construction boundary
for ExecutionContextCoordinator.

Factory-created coordinators preserve legacy update identity
semantics so existing callers that expect:

    updated is original

continue to work.
"""

from __future__ import annotations

from core.execution_context_coordinator import (
    ExecutionContextCoordinator,
)
from core.execution_context_service import (
    ExecutionContextService,
)
from core.execution_context_registry_service import (
    ExecutionContextRegistryService,
)


class ExecutionContextCoordinatorFactory:
    """
    Factory responsible for creating
    ExecutionContextCoordinator instances.
    """

    @staticmethod
    def create(
        context_service: ExecutionContextService | None = None,
        registry_service: (
            ExecutionContextRegistryService | None
        ) = None,
    ) -> ExecutionContextCoordinator:
        """
        Create a new ExecutionContextCoordinator.

        Every call returns a fresh coordinator instance.

        Factory-created coordinators intentionally enable
        identity-preserving update compatibility.

        This means:

            context = coordinator.create(...)
            updated = coordinator.update_metadata(...)

        satisfies:

            updated is context

        while direct ExecutionContextCoordinator instances
        retain immutable update behavior.
        """

        return ExecutionContextCoordinator(
            context_service=context_service,
            registry_service=registry_service,
            preserve_identity_on_update=True,
        )


__all__ = [
    "ExecutionContextCoordinatorFactory",
]