"""
Factory for execution context runtime coordinators.

Centralizes construction of isolated execution context
runtime coordinator instances.
"""

from __future__ import annotations

from core.execution_context_runtime_coordinator import (
    ExecutionContextRuntimeCoordinator,
)


class ExecutionContextRuntimeCoordinatorFactory:
    """Factory for creating execution context runtime coordinators."""

    @staticmethod
    def create() -> ExecutionContextRuntimeCoordinator:
        """
        Create a new isolated execution context runtime coordinator.

        Every factory call returns a completely independent
        coordinator instance.
        """

        return ExecutionContextRuntimeCoordinator()


__all__ = [
    "ExecutionContextRuntimeCoordinatorFactory",
]