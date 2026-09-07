"""
AI provider factory for AI Command Center.
"""

from __future__ import annotations

from ai.ollama_provider import OllamaProvider
from ai.provider import AIProvider
from config.settings import Settings
from core.result import Result


class AIProviderFactory:
    """Create configured AI providers."""

    @staticmethod
    def create(
        settings: Settings,
    ) -> Result[AIProvider]:
        """Create an AI provider from application settings."""

        provider = settings.ai_provider.strip().lower()

        if provider == "ollama":
            try:
                return Result.ok(
                    OllamaProvider(
                        base_url=settings.ollama_base_url,
                        model=settings.ai_model,
                    )
                )

            except ValueError as exc:
                return Result.fail(
                    "AI_PROVIDER_CONFIGURATION_ERROR",
                    str(exc),
                )

        return Result.fail(
            "UNSUPPORTED_AI_PROVIDER",
            f"Unsupported AI provider: {provider}",
            details={
                "provider": provider,
            },
        )
