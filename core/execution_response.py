"""
Standard execution response for AI Command Center.

Provides a consistent response contract for execution results,
including execution identity, plan information, output, errors,
and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ExecutionError:
    """Structured execution error."""

    code: str
    message: str
    details: dict[str, object] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class ExecutionResponse:
    """Standardized response returned by the execution layer."""

    success: bool

    execution_id: str

    plan_id: str | None = None

    output: Any = None

    error: ExecutionError | None = None

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    @classmethod
    def success_response(
        cls,
        *,
        execution_id: str,
        plan_id: str | None = None,
        output: Any = None,
        metadata: dict[str, object] | None = None,
    ) -> "ExecutionResponse":
        """Create a successful execution response."""

        normalized_execution_id = (
            execution_id.strip()
        )

        if not normalized_execution_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        return cls(
            success=True,
            execution_id=normalized_execution_id,
            plan_id=plan_id,
            output=output,
            error=None,
            metadata=dict(
                metadata or {}
            ),
        )

    @classmethod
    def failure_response(
        cls,
        *,
        execution_id: str,
        code: str,
        message: str,
        plan_id: str | None = None,
        details: dict[str, object] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "ExecutionResponse":
        """Create a failed execution response."""

        normalized_execution_id = (
            execution_id.strip()
        )

        if not normalized_execution_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        normalized_code = code.strip()

        if not normalized_code:
            raise ValueError(
                "Error code cannot be empty."
            )

        normalized_message = message.strip()

        if not normalized_message:
            raise ValueError(
                "Error message cannot be empty."
            )

        return cls(
            success=False,
            execution_id=normalized_execution_id,
            plan_id=plan_id,
            output=None,
            error=ExecutionError(
                code=normalized_code,
                message=normalized_message,
                details=dict(
                    details or {}
                ),
            ),
            metadata=dict(
                metadata or {}
            ),
        )

    def is_success(self) -> bool:
        """Return True when execution succeeded."""

        return self.success

    def is_failure(self) -> bool:
        """Return True when execution failed."""

        return not self.success

    def require_output(self) -> Any:
        """Return output or raise when execution failed."""

        if not self.success:
            message = (
                self.error.message
                if self.error
                else "Execution failed."
            )

            raise RuntimeError(message)

        return self.output

    def get_metadata(
        self,
        key: str,
        default: object | None = None,
    ) -> object | None:
        """Return response metadata."""

        return self.metadata.get(
            key,
            default,
        )