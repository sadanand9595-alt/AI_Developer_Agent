"""
Execution system factory for AI Command Center.

Centralizes construction of the complete execution subsystem
and keeps dependency wiring outside application code.
"""

from __future__ import annotations

from core.execution_coordinator import ExecutionCoordinator
from core.execution_facade import ExecutionFacade
from core.execution_system import ExecutionSystem


class ExecutionSystemFactory:
    """Factory for creating fully configured execution systems."""

    @staticmethod
    def create() -> ExecutionSystem:
        """Create a production-ready execution system."""

        facade = ExecutionFacade()

        coordinator = ExecutionCoordinator(
            facade=facade,
        )

        return ExecutionSystem(
            coordinator=coordinator,
        )


__all__ = [
    "ExecutionSystemFactory",
]