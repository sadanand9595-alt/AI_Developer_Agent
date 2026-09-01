"""
Execution context for AI Command Center.

The execution context carries the controlled runtime information
required by agents, tools, planners, validators, and executors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from core.types import (
    AgentId,
    ConversationId,
    ExecutionId,
    SessionId,
    TaskId,
    UserId,
)


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """
    Immutable context shared during a task execution.

    The context does not contain secrets such as API keys or
    passwords. Sensitive credentials must be handled by the
    dedicated security/configuration layers.
    """

    user_id: UserId
    task_id: TaskId

    session_id: SessionId | None = None
    conversation_id: ConversationId | None = None
    agent_id: AgentId | None = None
    execution_id: ExecutionId = field(
        default_factory=lambda: ExecutionId(str(uuid4()))
    )
    lease_owner_id: str | None = None

    workspace_root: str = "."
    working_directory: str = "."

    permissions: frozenset[str] = field(
        default_factory=frozenset
    )

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        task_id: str,
        session_id: str | None = None,
        conversation_id: str | None = None,
        agent_id: str | None = None,
        execution_id: str | None = None,
        lease_owner_id: str | None = None,
        workspace_root: str = ".",
        working_directory: str = ".",
        permissions: set[str] | frozenset[str] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "ExecutionContext":
        """
        Create a validated execution context.
        """

        if (
            not isinstance(user_id, str)
            or not user_id.strip()
        ):
            raise ValueError(
                "User ID must be a non-empty string."
            )

        if (
            not isinstance(task_id, str)
            or not task_id.strip()
        ):
            raise ValueError(
                "Task ID must be a non-empty string."
            )

        if permissions is not None and not isinstance(
            permissions,
            (set, frozenset),
        ):
            raise ValueError(
                "Permissions must be a set or frozenset."
            )

        if metadata is not None and not isinstance(
            metadata,
            dict,
        ):
            raise ValueError(
                "Metadata must be a dictionary."
            )

        normalized_execution_id = (
            execution_id.strip()
            if isinstance(execution_id, str)
            else None
        )
        normalized_lease_owner_id = (
            lease_owner_id.strip()
            if isinstance(lease_owner_id, str)
            else None
        )
        resolved_execution_id = (
            normalized_execution_id
            if normalized_execution_id
            else str(uuid4())
        )
        resolved_lease_owner_id = (
            normalized_lease_owner_id
            if normalized_lease_owner_id
            else resolved_execution_id
        )

        if resolved_lease_owner_id != resolved_execution_id:
            raise ValueError(
                "lease_owner_id must match execution_id in ExecutionContext."
            )

        return cls(
            user_id=UserId(user_id),
            task_id=TaskId(task_id),
            session_id=(
                SessionId(session_id)
                if session_id
                else None
            ),
            conversation_id=(
                ConversationId(conversation_id)
                if conversation_id
                else None
            ),
            agent_id=(
                AgentId(agent_id)
                if agent_id
                else None
            ),
            execution_id=ExecutionId(resolved_execution_id),
            lease_owner_id=resolved_lease_owner_id,
            workspace_root=workspace_root,
            working_directory=working_directory,
            permissions=frozenset(
                permissions or set()
            ),
            metadata=dict(metadata or {}),
        )

    def has_permission(self, permission: str) -> bool:
        """Return whether this context has a specific permission."""

        return permission in self.permissions

    def require_permission(self, permission: str) -> None:
        """
        Validate that the context has a required permission.

        Raises:
            PermissionError: If the permission is unavailable.
        """

        if not self.has_permission(permission):
            raise PermissionError(
                f"Required permission is missing: {permission}"
            )

    def with_agent(
        self,
        agent_id: str,
    ) -> "ExecutionContext":
        """Return a new context associated with an agent."""

        return ExecutionContext(
            user_id=self.user_id,
            task_id=self.task_id,
            session_id=self.session_id,
            conversation_id=self.conversation_id,
            agent_id=AgentId(agent_id),
            execution_id=self.execution_id,
            lease_owner_id=self.lease_owner_id,
            workspace_root=self.workspace_root,
            working_directory=self.working_directory,
            permissions=self.permissions,
            metadata=dict(self.metadata),
            created_at=self.created_at,
        )

    def with_working_directory(
        self,
        working_directory: str,
    ) -> "ExecutionContext":
        """Return a new context with a different working directory."""

        return ExecutionContext(
            user_id=self.user_id,
            task_id=self.task_id,
            session_id=self.session_id,
            conversation_id=self.conversation_id,
            agent_id=self.agent_id,
            execution_id=self.execution_id,
            lease_owner_id=self.lease_owner_id,
            workspace_root=self.workspace_root,
            working_directory=working_directory,
            permissions=self.permissions,
            metadata=dict(self.metadata),
            created_at=self.created_at,
        )