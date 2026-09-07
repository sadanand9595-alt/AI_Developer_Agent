"""
AI actions for AI Command Center.
"""

from __future__ import annotations

from ai.provider import AIProvider
from core.pipeline_context import PipelineContext
from core.result import Result


class AIActions:
    """Collection of AI-backed execution actions."""

    def __init__(
        self,
        provider: AIProvider,
    ) -> None:
        if not isinstance(
            provider,
            AIProvider,
        ):
            raise TypeError(
                "Expected an AIProvider instance."
            )

        self._provider = provider

    def generate_code(
        self,
        context: PipelineContext,
    ) -> Result[object]:
        """Generate code from the current execution request."""

        if not isinstance(
            context,
            PipelineContext,
        ):
            return Result.fail(
                "INVALID_PIPELINE_CONTEXT",
                "Expected a PipelineContext instance.",
            )

        request = context.get_metadata(
            "request"
        )

        if not isinstance(
            request,
            str,
        ) or not request.strip():
            return Result.fail(
                "MISSING_AI_REQUEST",
                "AI request is missing from the pipeline context.",
            )

        prompt = (
            "You are a coding agent inside AI Command Center.\n\n"
            "Generate the requested code.\n"
            "Return only the code unless explanation is explicitly requested.\n\n"
            "User request:\n"
            f"{request}"
        )

        result = self._provider.generate(
            prompt
        )

        if result.is_failure():
            return Result.fail(
                result.error.code,
                result.error.message,
                details=result.error.details,
            )

        generated_code = result.require_data()

        if not isinstance(
            generated_code,
            str,
        ):
            return Result.fail(
                "INVALID_GENERATED_CODE",
                "AI provider returned non-string code output.",
            )

        cleaned_code = self._normalize_code_output(
            generated_code
        )

        return Result.ok(
            cleaned_code
        )

    @staticmethod
    def _normalize_code_output(
        code: str,
    ) -> str:
        """
        Remove common Markdown code fences from AI-generated source code.

        Examples:

            ```python
            def hello():
                return "Hello"
            ```

        becomes:

            def hello():
                return "Hello"
        """

        text = code.strip()

        if not text:
            return text

        lines = text.splitlines()

        # Remove opening Markdown fence such as:
        # ```python
        # ```py
        # ```
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        # Remove closing Markdown fence.
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        return "\n".join(lines).strip()
