"""
Execution-specific context for AI Command Center.

Provides immutable contextual information associated with a
single execution instance.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Immutable context associated with one execution."""

    execution_id: str
    task_id: str | None = None
    session_id: str | None = None
    agent_id: str | None = None

    workspace_root: str = "."
    working_directory: str = "."

    permissions: frozenset[str] = field(
        default_factory=frozenset
    )

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    context_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    def __post_init__(self) -> None:
        """
        Normalize mutable values after construction.

        The dataclass itself is frozen, but dictionaries are
        mutable. Therefore metadata is deep-copied so that
        external dictionaries cannot accidentally mutate the
        context.
        """

        object.__setattr__(
            self,
            "metadata",
            deepcopy(self.metadata),
        )

        object.__setattr__(
            self,
            "permissions",
            frozenset(self.permissions),
        )

    @classmethod
    def create(
        cls,
        *,
        execution_id: str,
        task_id: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
        workspace_root: str = ".",
        working_directory: str = ".",
        permissions: set[str]
        | frozenset[str]
        | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "ExecutionContext":
        """Create a validated execution context."""

        normalized_execution_id = (
            execution_id.strip()
        )

        if not normalized_execution_id:
            raise ValueError(
                "Execution ID cannot be empty."
            )

        return cls(
            execution_id=normalized_execution_id,
            task_id=task_id,
            session_id=session_id,
            agent_id=agent_id,
            workspace_root=workspace_root,
            working_directory=working_directory,
            permissions=frozenset(
                permissions or set()
            ),
            metadata=deepcopy(
                metadata or {}
            ),
        )

    def has_permission(
        self,
        permission: str,
    ) -> bool:
        """Return whether the context has a permission."""

        return permission in self.permissions

    def require_permission(
        self,
        permission: str,
    ) -> None:
        """Raise PermissionError when permission is missing."""

        if not self.has_permission(
            permission
        ):
            raise PermissionError(
                (
                    "Required permission is missing: "
                    f"{permission}"
                )
            )

    def with_metadata(
        self,
        **updates: object,
    ) -> "ExecutionContext":
        """
        Return a new context with updated metadata.

        The original context metadata is never modified.
        A deep copy is used so nested mutable values are also
        isolated between the original and updated contexts.
        """

        metadata = deepcopy(
            self.metadata
        )

        metadata.update(
            deepcopy(updates)
        )

        return ExecutionContext(
            execution_id=self.execution_id,
            task_id=self.task_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            workspace_root=self.workspace_root,
            working_directory=self.working_directory,
            permissions=self.permissions,
            metadata=metadata,
            context_id=self.context_id,
            created_at=self.created_at,
        )

    def with_working_directory(
        self,
        working_directory: str,
    ) -> "ExecutionContext":
        """
        Return a new context with a different working directory.

        Metadata is deeply copied so the original context remains
        isolated.
        """

        return ExecutionContext(
            execution_id=self.execution_id,
            task_id=self.task_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            workspace_root=self.workspace_root,
            working_directory=working_directory,
            permissions=self.permissions,
            metadata=deepcopy(
                self.metadata
            ),
            context_id=self.context_id,
            created_at=self.created_at,
        )

    def with_agent(
        self,
        agent_id: str,
    ) -> "ExecutionContext":
        """
        Return a new context associated with an agent.

        Metadata is deeply copied so the original context remains
        isolated.
        """

        return ExecutionContext(
            execution_id=self.execution_id,
            task_id=self.task_id,
            session_id=self.session_id,
            agent_id=agent_id,
            workspace_root=self.workspace_root,
            working_directory=self.working_directory,
            permissions=self.permissions,
            metadata=deepcopy(
                self.metadata
            ),
            context_id=self.context_id,
            created_at=self.created_at,
        )


__all__ = [
    "ExecutionContext",
]