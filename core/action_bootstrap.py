"""
Action registration bootstrap for AI Command Center.
"""

from __future__ import annotations

from actions.ai_actions import AIActions
from actions.file_actions import FileActions
from ai.provider import AIProvider
from core.action_registry import ActionRegistry
from core.result import Result


class ActionBootstrap:
    """Register application actions."""

    @staticmethod
    def register_ai_actions(
        registry: ActionRegistry,
        provider: AIProvider,
    ) -> Result[None]:
        """Register AI-backed actions."""

        if not isinstance(
            registry,
            ActionRegistry,
        ):
            return Result.fail(
                "INVALID_ACTION_REGISTRY",
                "Expected an ActionRegistry instance.",
            )

        if not isinstance(
            provider,
            AIProvider,
        ):
            return Result.fail(
                "INVALID_AI_PROVIDER",
                "Expected an AIProvider instance.",
            )

        ai_actions = AIActions(
            provider
        )

        result = registry.register(
            "generate_code",
            ai_actions.generate_code,
        )

        if result.is_failure():
            return Result.fail(
                result.error.code,
                result.error.message,
                details=result.error.details,
            )

        return Result.ok()

    @staticmethod
    def register_file_actions(
        registry: ActionRegistry,
    ) -> Result[None]:
        """Register filesystem actions."""

        if not isinstance(
            registry,
            ActionRegistry,
        ):
            return Result.fail(
                "INVALID_ACTION_REGISTRY",
                "Expected an ActionRegistry instance.",
            )

        file_actions = FileActions()

        result = registry.register(
            "write_file",
            file_actions.write_file,
        )

        if result.is_failure():
            return Result.fail(
                result.error.code,
                result.error.message,
                details=result.error.details,
            )

        return Result.ok()

    @staticmethod
    def register_all(
        registry: ActionRegistry,
        provider: AIProvider,
    ) -> Result[None]:
        """Register all application actions."""

        ai_result = ActionBootstrap.register_ai_actions(
            registry,
            provider,
        )

        if ai_result.is_failure():
            return Result.fail(
                ai_result.error.code,
                ai_result.error.message,
                details=ai_result.error.details,
            )

        file_result = ActionBootstrap.register_file_actions(
            registry,
        )

        if file_result.is_failure():
            return Result.fail(
                file_result.error.code,
                file_result.error.message,
                details=file_result.error.details,
            )

        return Result.ok()


__all__ = [
    "ActionBootstrap",
]
