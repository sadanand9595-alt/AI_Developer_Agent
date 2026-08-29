"""
Event definitions for AI Command Center.

Events provide a structured way for different parts of the
system to communicate without creating tight dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class EventType(StrEnum):
    """Supported application lifecycle events."""

    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    PLANNING_STARTED = "planning.started"
    PLANNING_COMPLETED = "planning.completed"
    PLANNING_FAILED = "planning.failed"

    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    TOOL_CALLED = "tool.called"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"

    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_REJECTED = "approval.rejected"

    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"

    VALIDATION_STARTED = "validation.started"
    VALIDATION_PASSED = "validation.passed"
    VALIDATION_FAILED = "validation.failed"

    SELF_CORRECTION_STARTED = "self_correction.started"
    SELF_CORRECTION_COMPLETED = "self_correction.completed"
    SELF_CORRECTION_FAILED = "self_correction.failed"


@dataclass(frozen=True, slots=True)
class Event:
    """
    Base event object.

    Every event has a unique ID, type, timestamp, and payload.
    """

    event_type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the event into a serializable dictionary."""

        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "created_at": self.created_at.isoformat(),
            "payload": self.payload,
        }


@dataclass(frozen=True, slots=True)
class TaskEvent(Event):
    """Event associated with a task."""

    task_id: str = ""


@dataclass(frozen=True, slots=True)
class AgentEvent(Event):
    """Event associated with an agent."""

    agent_id: str = ""
    task_id: str | None = None


@dataclass(frozen=True, slots=True)
class ToolEvent(Event):
    """Event associated with a tool execution."""

    tool_id: str = ""
    task_id: str | None = None
    agent_id: str | None = None


@dataclass(frozen=True, slots=True)
class ApprovalEvent(Event):
    """Event associated with human approval."""

    approval_id: str = ""
    task_id: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationEvent(Event):
    """Event associated with validation."""

    task_id: str | None = None
    execution_id: str | None = None