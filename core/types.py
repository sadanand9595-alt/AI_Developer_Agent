"""
Shared type definitions for AI Command Center.

These types provide common identifiers and status values used
across commands, agents, tools, tasks, and execution flows.
"""

from __future__ import annotations

from enum import StrEnum
from typing import NewType


# ---------------------------------------------------------------------------
# Strongly typed identifiers
# ---------------------------------------------------------------------------

UserId = NewType("UserId", str)
SessionId = NewType("SessionId", str)
ConversationId = NewType("ConversationId", str)
TaskId = NewType("TaskId", str)
AgentId = NewType("AgentId", str)
ToolId = NewType("ToolId", str)
ExecutionId = NewType("ExecutionId", str)
ApprovalId = NewType("ApprovalId", str)


# ---------------------------------------------------------------------------
# Common status types
# ---------------------------------------------------------------------------


class TaskStatus(StrEnum):
    """Lifecycle status of an AI task."""

    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStatus(StrEnum):
    """Status of a tool or agent execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ApprovalStatus(StrEnum):
    """Status of a human approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AgentStatus(StrEnum):
    """Operational status of an agent."""

    IDLE = "idle"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"
    DISABLED = "disabled"


class ToolRiskLevel(StrEnum):
    """Risk classification for tools."""

    READ_ONLY = "read_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PermissionAction(StrEnum):
    """Actions that can be authorized by the security layer."""

    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    EXTERNAL = "external"