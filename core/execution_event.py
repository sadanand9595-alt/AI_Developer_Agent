"""
Execution events for AI Command Center.

Defines immutable event objects used to describe execution
lifecycle, progress, and failure changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class ExecutionEventType:
    """Standard execution event types."""

    STARTED = "execution.started"
    STEP_STARTED = "execution.step_started"
    STEP_COMPLETED = "execution.step_completed"
    COMPLETED = "execution.completed"
    FAILED = "execution.failed"
    CANCELLED = "execution.cancelled"


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    """Immutable execution event."""

    event_type: str
    execution_id: str

    task_id: str | None = None
    step_name: str | None = None

    data: Any = None

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        execution_id: str,
        task_id: str | None = None,
        step_name: str | None = None,
        data: Any = None,
    ) -> "ExecutionEvent":
        """Create a validated execution event."""

        normalized_type = event_type.strip()
        normalized_execution_id = execution_id.strip()

        if not normalized_type:
            raise ValueError(
                "Event type cannot be empty."
            )

        if not normalized_execution_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        normalized_step_name = (
            step_name.strip()
            if isinstance(step_name, str)
            else None
        )

        return cls(
            event_type=normalized_type,
            execution_id=normalized_execution_id,
            task_id=task_id,
            step_name=normalized_step_name,
            data=data,
        )

    def is_type(
        self,
        event_type: str,
    ) -> bool:
        """Return whether this event has the given type."""

        return self.event_type == event_type.strip()

    def is_terminal(self) -> bool:
        """Return whether this event represents a terminal state."""

        return self.event_type in {
            ExecutionEventType.COMPLETED,
            ExecutionEventType.FAILED,
            ExecutionEventType.CANCELLED,
        }

    def is_step_event(self) -> bool:
        """Return whether this event relates to a step."""

        return self.event_type in {
            ExecutionEventType.STEP_STARTED,
            ExecutionEventType.STEP_COMPLETED,
        }