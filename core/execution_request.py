"""
Structured execution request for AI Command Center.

Defines the validated input contract used by the execution
engine and future AI planning components.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """Immutable request submitted to the execution engine."""

    request: str

    user_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None

    session_id: str | None = None
    conversation_id: str | None = None

    workspace_root: str = "."
    working_directory: str = "."

    permissions: frozenset[str] = field(
        default_factory=frozenset
    )

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    @classmethod
    def create(
        cls,
        *,
        request: str,
        user_id: str | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        conversation_id: str | None = None,
        workspace_root: str = ".",
        working_directory: str = ".",
        permissions: set[str]
        | frozenset[str]
        | None = None,
        metadata: dict[str, object]
        | None = None,
    ) -> "ExecutionRequest":
        """Create a normalized execution request."""

        if not isinstance(request, str):
            raise ValueError(
                "Execution request must be a string."
            )

        normalized_request = request.strip()

        if not normalized_request:
            raise ValueError(
                "Execution request cannot be empty."
            )

        if not isinstance(workspace_root, str):
            raise ValueError(
                "workspace_root must be a string."
            )

        if not isinstance(working_directory, str):
            raise ValueError(
                "working_directory must be a string."
            )

        normalized_workspace = (
            workspace_root.strip()
            or "."
        )

        normalized_working_directory = (
            working_directory.strip()
            or "."
        )

        return cls(
            request=normalized_request,
            user_id=user_id,
            task_id=task_id,
            agent_id=agent_id,
            session_id=session_id,
            conversation_id=conversation_id,
            workspace_root=normalized_workspace,
            working_directory=(
                normalized_working_directory
            ),
            permissions=frozenset(
                permissions or set()
            ),
            metadata=dict(
                metadata or {}
            ),
        )

    def has_permission(
        self,
        permission: str,
    ) -> bool:
        """Return whether the request has a permission."""

        return permission in self.permissions

    def with_metadata(
        self,
        key: str,
        value: object,
    ) -> "ExecutionRequest":
        """Return a new request with additional metadata."""

        if not isinstance(key, str):
            raise ValueError(
                "Metadata key must be a string."
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "Metadata key cannot be empty."
            )

        updated_metadata = dict(
            self.metadata
        )

        updated_metadata[
            normalized_key
        ] = value

        return ExecutionRequest(
            request=self.request,
            user_id=self.user_id,
            task_id=self.task_id,
            agent_id=self.agent_id,
            session_id=self.session_id,
            conversation_id=self.conversation_id,
            workspace_root=self.workspace_root,
            working_directory=self.working_directory,
            permissions=self.permissions,
            metadata=updated_metadata,
        )