"""
Standard result objects for AI Command Center.

All major subsystems should return structured results instead
of relying on inconsistent dictionaries or raw values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """Structured information about a failed operation."""

    code: str
    message: str
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    """
    Generic success/failure result.

    A successful result contains `data`.
    A failed result contains `error`.
    """

    success: bool
    data: T | None = None
    error: ErrorInfo | None = None

    @classmethod
    def ok(cls, data: T | None = None) -> "Result[T]":
        """Create a successful result."""
        return cls(
            success=True,
            data=data,
            error=None,
        )

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> "Result[T]":
        """Create a failed result."""
        return cls(
            success=False,
            data=None,
            error=ErrorInfo(
                code=code,
                message=message,
                details=details or {},
            ),
        )

    def is_success(self) -> bool:
        """Return True when the operation succeeded."""
        return self.success

    def is_failure(self) -> bool:
        """Return True when the operation failed."""
        return not self.success

    def require_data(self) -> T:
        """
        Return result data or raise an error.

        This should only be used when the caller expects
        a successful result.
        """

        if not self.success:
            message = (
                self.error.message
                if self.error
                else "Operation failed."
            )

            raise RuntimeError(message)

        return self.data  # type: ignore[return-value]