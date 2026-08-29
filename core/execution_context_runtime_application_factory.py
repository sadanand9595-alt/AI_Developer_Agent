"""
Factory for ExecutionContextRuntimeApplication.

Centralizes construction of the runtime application layer.
"""

from __future__ import annotations

from core.execution_context_runtime_application import (
    ExecutionContextRuntimeApplication,
)
from core.execution_context_runtime_coordinator_factory import (
    ExecutionContextRuntimeCoordinatorFactory,
)


class ExecutionContextRuntimeApplicationFactory:
    """Factory for creating runtime applications."""

    @staticmethod
    def create() -> ExecutionContextRuntimeApplication:
        """Create an isolated runtime application."""

        coordinator = (
            ExecutionContextRuntimeCoordinatorFactory.create()
        )

        return ExecutionContextRuntimeApplication(
            coordinator=coordinator,
        )


__all__ = [
    "ExecutionContextRuntimeApplicationFactory",
]