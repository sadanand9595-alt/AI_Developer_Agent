"""
Factory for execution context registry services.

Centralizes construction of the execution context registry layer.
"""

from __future__ import annotations

from core.execution_context_registry import (
    ExecutionContextRegistry,
)
from core.execution_context_registry_service import (
    ExecutionContextRegistryService,
)


class ExecutionContextRegistryFactory:
    """Factory for creating execution context registry services."""

    @staticmethod
    def create() -> ExecutionContextRegistryService:
        """Create an isolated execution context registry service."""

        registry = ExecutionContextRegistry()

        return ExecutionContextRegistryService(
            registry
        )


__all__ = [
    "ExecutionContextRegistryFactory",
]
