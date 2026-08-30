"""
Runtime state for an active execution context.

ExecutionContext contains immutable execution identity and
configuration. ExecutionContextRuntime contains mutable
operational state associated with that context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any


@dataclass(slots=True)
class ExecutionContextRuntime:
    """Mutable runtime state for one execution context."""

    context_id: str

    active: bool = True
    paused: bool = False

    current_step: str | None = None
    completed_steps: int = 0
    failed_steps: int = 0

    variables: dict[str, Any] = field(
        default_factory=dict
    )

    started_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    stopped_at: datetime | None = None

    _lock: RLock = field(
        default_factory=RLock,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """Validate runtime identity."""

        if not self.context_id.strip():
            raise ValueError(
                "Context ID cannot be empty."
            )

    def start_step(
        self,
        step_name: str,
    ) -> None:
        """Mark a step as the current active step."""

        normalized_name = step_name.strip()

        if not normalized_name:
            raise ValueError(
                "Step name cannot be empty."
            )

        with self._lock:
            self._ensure_active()

            self.current_step = normalized_name
            self.updated_at = datetime.now(
                timezone.utc
            )

    def complete_step(
        self,
    ) -> None:
        """Complete the current step."""

        with self._lock:
            self._ensure_active()

            if self.current_step is None:
                raise RuntimeError(
                    "No active step to complete."
                )

            self.completed_steps += 1
            self.current_step = None
            self.updated_at = datetime.now(
                timezone.utc
            )

    def fail_step(
        self,
    ) -> None:
        """Mark the current step as failed."""

        with self._lock:
            self._ensure_active()

            if self.current_step is None:
                raise RuntimeError(
                    "No active step to fail."
                )

            self.failed_steps += 1
            self.current_step = None
            self.updated_at = datetime.now(
                timezone.utc
            )

    def set_variable(
        self,
        name: str,
        value: Any,
    ) -> None:
        """Set a runtime variable."""

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Variable name cannot be empty."
            )

        with self._lock:
            self._ensure_active()

            self.variables[
                normalized_name
            ] = value

            self.updated_at = datetime.now(
                timezone.utc
            )

    def get_variable(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """Return a runtime variable."""

        normalized_name = name.strip()

        if not normalized_name:
            return default

        with self._lock:
            return self.variables.get(
                normalized_name,
                default,
            )

    def remove_variable(
        self,
        name: str,
    ) -> bool:
        """Remove a runtime variable."""

        normalized_name = name.strip()

        if not normalized_name:
            return False

        with self._lock:
            self._ensure_active()

            if normalized_name not in self.variables:
                return False

            del self.variables[
                normalized_name
            ]

            self.updated_at = datetime.now(
                timezone.utc
            )

            return True

    def pause(self) -> None:
        """Pause the active runtime."""

        with self._lock:
            self._ensure_active()

            if self.paused:
                return

            self.paused = True
            self.updated_at = datetime.now(
                timezone.utc
            )

    def resume(self) -> None:
        """Resume a paused runtime."""

        with self._lock:
            self._ensure_active()

            if not self.paused:
                return

            self.paused = False
            self.updated_at = datetime.now(
                timezone.utc
            )

    def stop(self) -> None:
        """Stop the runtime."""

        with self._lock:
            if not self.active:
                return

            self.active = False
            self.paused = False
            self.current_step = None
            self.stopped_at = datetime.now(
                timezone.utc
            )
            self.updated_at = self.stopped_at

    def snapshot(
        self,
    ) -> dict[str, object]:
        """Return a consistent runtime snapshot."""

        with self._lock:
            return {
                "context_id": self.context_id,
                "active": self.active,
                "paused": self.paused,
                "current_step": self.current_step,
                "completed_steps": self.completed_steps,
                "failed_steps": self.failed_steps,
                "variables": dict(
                    self.variables
                ),
                "started_at": self.started_at,
                "updated_at": self.updated_at,
                "stopped_at": self.stopped_at,
            }

    def _ensure_active(self) -> None:
        """Ensure runtime is still active."""

        if not self.active:
            raise RuntimeError(
                "Execution context runtime is stopped."
            )


__all__ = [
    "ExecutionContextRuntime",
]
