"""
Factory for ExecutionContextApplication.

Centralizes construction of the application-facing
execution context subsystem.
"""

from __future__ import annotations

from core.execution_context_application import (
    ExecutionContextApplication,
)
from core.execution_context_coordinator_factory import (
    ExecutionContextCoordinatorFactory,
)


class ExecutionContextApplicationFactory:
    """Factory for creating execution context applications."""

    @staticmethod
    def create() -> ExecutionContextApplication:
        """Create an isolated execution context application."""

        coordinator = (
            ExecutionContextCoordinatorFactory.create()
        )

        return ExecutionContextApplication(
            coordinator=coordinator,
        )


__all__ = [
    "ExecutionContextApplicationFactory",
]