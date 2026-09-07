"""
Execution system factory for AI Command Center.

Centralizes construction of the complete execution subsystem
and keeps dependency wiring outside application code.
"""

from __future__ import annotations

from ai.factory import AIProviderFactory
from ai.provider import AIProvider
from config.settings import get_settings
from core.action_bootstrap import ActionBootstrap
from core.action_registry import ActionRegistry
from core.execution_coordinator import ExecutionCoordinator
from core.execution_facade import ExecutionFacade
from core.execution_system import ExecutionSystem
from core.result import Result


class ExecutionSystemFactory:
    """Factory for creating fully configured execution systems."""

    @staticmethod
    def create() -> ExecutionSystem:
        """Create a production-ready execution system."""

        settings = get_settings()
        provider_result = AIProviderFactory.create(settings)

        if provider_result.is_failure():
            raise RuntimeError(
                f"{provider_result.error.code}: "
                f"{provider_result.error.message}"
            )

        return ExecutionSystemFactory.create_with_provider(
            provider_result.require_data()
        )

    @staticmethod
    def create_with_provider(provider: AIProvider) -> ExecutionSystem:
        """Create an execution system using an existing AI provider."""

        registry = ActionRegistry()

        registration_result = ActionBootstrap.register_all(
            registry,
            provider,
        )

        if registration_result.is_failure():
            raise RuntimeError(
                f"{registration_result.error.code}: "
                f"{registration_result.error.message}"
            )

        facade = ExecutionFacade()

        coordinator = ExecutionCoordinator(
            registry=registry,
            facade=facade,
        )

        return ExecutionSystem(
            coordinator=coordinator,
        )

    @staticmethod
    def create_result() -> Result[ExecutionSystem]:
        """Create an execution system while preserving failures as a Result."""

        try:
            return Result.ok(
                ExecutionSystemFactory.create()
            )
        except (RuntimeError, ValueError) as exc:
            return Result.fail(
                "EXECUTION_SYSTEM_FACTORY_ERROR",
                str(exc),
            )


__all__ = [
    "ExecutionSystemFactory",
]
