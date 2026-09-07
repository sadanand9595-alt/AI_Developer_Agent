"""
Ollama AI provider for AI Command Center.
"""

from __future__ import annotations

import httpx

from ai.provider import AIProvider
from core.result import Result


class OllamaProvider(AIProvider):
    """Generate responses through the Ollama REST API."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout: float = 120.0,
    ) -> None:
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError(
                "Ollama base URL cannot be empty."
            )

        if not isinstance(model, str) or not model.strip():
            raise ValueError(
                "Ollama model cannot be empty."
            )

        if timeout <= 0:
            raise ValueError(
                "Ollama timeout must be greater than zero."
            )

        self._base_url = base_url.rstrip("/")
        self._model = model.strip()
        self._timeout = timeout

    @property
    def model(self) -> str:
        """Return the configured Ollama model."""

        return self._model

    @property
    def base_url(self) -> str:
        """Return the configured Ollama base URL."""

        return self._base_url

    def generate(
        self,
        prompt: str,
    ) -> Result[str]:
        """Generate text using Ollama."""

        if not isinstance(prompt, str):
            return Result.fail(
                "INVALID_AI_PROMPT",
                "AI prompt must be a string.",
            )

        normalized_prompt = prompt.strip()

        if not normalized_prompt:
            return Result.fail(
                "EMPTY_AI_PROMPT",
                "AI prompt cannot be empty.",
            )

        payload = {
            "model": self._model,
            "prompt": normalized_prompt,
            "stream": False,
        }

        try:
            response = httpx.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=self._timeout,
            )

        except httpx.TimeoutException as exc:
            return Result.fail(
                "AI_PROVIDER_TIMEOUT",
                "Ollama request timed out.",
                details={
                    "provider": "ollama",
                    "model": self._model,
                    "exception_type": type(exc).__name__,
                },
            )

        except httpx.HTTPError as exc:
            return Result.fail(
                "AI_PROVIDER_CONNECTION_ERROR",
                str(exc),
                details={
                    "provider": "ollama",
                    "model": self._model,
                    "exception_type": type(exc).__name__,
                },
            )

        except Exception as exc:
            return Result.fail(
                "AI_PROVIDER_ERROR",
                str(exc),
                details={
                    "provider": "ollama",
                    "model": self._model,
                    "exception_type": type(exc).__name__,
                },
            )

        if response.status_code >= 400:
            return Result.fail(
                "AI_PROVIDER_HTTP_ERROR",
                (
                    f"Ollama returned HTTP "
                    f"{response.status_code}."
                ),
                details={
                    "provider": "ollama",
                    "model": self._model,
                    "status_code": response.status_code,
                    "response": response.text[:1000],
                },
            )

        try:
            data = response.json()

        except ValueError as exc:
            return Result.fail(
                "AI_PROVIDER_INVALID_RESPONSE",
                "Ollama returned invalid JSON.",
                details={
                    "provider": "ollama",
                    "model": self._model,
                    "exception_type": type(exc).__name__,
                },
            )

        generated = data.get("response")

        if not isinstance(generated, str):
            return Result.fail(
                "AI_PROVIDER_INVALID_RESPONSE",
                "Ollama response did not contain text.",
                details={
                    "provider": "ollama",
                    "model": self._model,
                },
            )

        return Result.ok(
            generated
        )
