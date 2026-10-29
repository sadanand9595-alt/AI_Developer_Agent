"""
Pydantic request/response schemas for the API layer.

These are transport-layer contracts only. They validate external
input shape (types, required fields, basic constraints) before it
ever reaches a service. Business-rule validation remains in the
already-audited services/repositories.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    is_active: bool
    is_admin: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)
    conversation_id: str | None = None
    priority: int = Field(default=0, ge=0)


class TaskCompleteRequest(BaseModel):
    result: dict[str, Any] | None = None


class TaskFailRequest(BaseModel):
    error: dict[str, Any] | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    description: str
    status: str
    priority: int
    retry_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    agent_type: str = Field(min_length=1, max_length=100)
    description: str | None = None
    model_provider: str | None = Field(default=None, max_length=100)
    model_name: str | None = Field(default=None, max_length=200)
    capabilities: list[str] | None = None
    configuration: dict[str, Any] | None = None
    max_iterations: int = Field(default=10, ge=1)

    @field_validator("name", "agent_type")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Value cannot be blank.")

        return value


class AgentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    agent_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = None
    model_provider: str | None = Field(default=None, max_length=100)
    model_name: str | None = Field(default=None, max_length=200)
    capabilities: list[str] | None = None
    configuration: dict[str, Any] | None = None
    max_iterations: int | None = Field(default=None, ge=1)

    @field_validator("name", "agent_type")
    @classmethod
    def validate_non_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Value cannot be blank.")

        return value


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    agent_type: str
    model_provider: str | None
    model_name: str | None
    capabilities: list[str] | None
    configuration: dict[str, Any] | None
    status: str
    is_enabled: bool
    max_iterations: int
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime | None


class AgentExecuteRequest(BaseModel):
    request: str = Field(min_length=1)


class AgentExecuteResponse(BaseModel):
    execution_id: str
    task_id: str
    agent_id: str
    status: str
    output: Any = None
    metadata: dict[str, Any]

# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    system_context: str | None = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    tool_name: str | None
    created_at: datetime


class AIMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------


class ApprovalActionRequest(BaseModel):
    comment: str | None = None


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    execution_id: str | None = None
    plan_id: str | None = None
    step_id: str | None = None
    action: str
    reason: str
    requested_operation: str
    status: str
    requested_at: datetime
    reviewed_at: datetime | None


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

class AgentExecutionResponse(BaseModel):
    """Durable execution history exposed through the Agent API."""

    execution_id: str
    task_id: str
    agent_id: str
    status: str
    title: str
    description: str
    priority: int
    retry_count: int
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime

class ExecutionStatusResponse(BaseModel):
    """Unified durable execution status."""

    execution_id: str
    task_id: str
    agent_id: str | None
    status: str
    title: str
    description: str
    priority: int
    retry_count: int
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime

class ExecutionStatusResponse(BaseModel):
    """Unified durable execution status."""

    execution_id: str
    task_id: str
    agent_id: str | None
    status: str
    title: str
    description: str
    priority: int
    retry_count: int
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime


# ---------------------------------------------------------------------------
# Sequential Orchestration
# ---------------------------------------------------------------------------

class OrchestrationSpecialistRequest(BaseModel):
    """One specialist in a sequential orchestration request."""

    agent_id: str = Field(min_length=1, max_length=200)
    name: str | None = Field(default=None, max_length=200)


class SequentialOrchestrationRequest(BaseModel):
    """Request to execute specialists sequentially."""

    request: str = Field(min_length=1)
    specialists: list[OrchestrationSpecialistRequest] = Field(min_length=1)
    title: str = Field(
        default="Sequential Agent Orchestration",
        min_length=1,
        max_length=500,
    )


class SequentialOrchestrationResponse(BaseModel):
    """Result of a sequential specialist orchestration."""

    task_id: str
    execution_id: str
    status: str
    partial_result: bool
    successful_count: int
    failed_count: int
    specialists: list[dict[str, Any]]
    final_output: Any | None = None
    error: dict[str, Any] | None = None
