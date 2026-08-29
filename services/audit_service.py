"""
Audit service for AI Command Center.

Contains business logic for recording and retrieving
system audit events.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.models.audit import AuditLog
from database.repositories.audit_repository import AuditRepository


class AuditService:
    """Business operations for audit logging."""

    def __init__(self, session: Session) -> None:
        self._repository = AuditRepository(session)

    def record_event(
        self,
        *,
        action: str,
        category: str,
        status: str,
        user_id: str | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
        tool_id: str | None = None,
        message: str | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Record a system audit event."""

        return self._repository.create(
            action=action,
            category=category,
            status=status,
            user_id=user_id,
            task_id=task_id,
            agent_id=agent_id,
            tool_id=tool_id,
            message=message,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def get_event(
        self,
        audit_id: str,
    ) -> AuditLog | None:
        """Get an audit event by ID."""

        return self._repository.get_by_id(audit_id)

    def get_user_events(
        self,
        user_id: str,
        *,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Return recent audit events for a user."""

        return self._repository.list_by_user(
            user_id,
            limit=limit,
        )

    def get_task_events(
        self,
        task_id: str,
        *,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Return audit events for a task."""

        return self._repository.list_by_task(
            task_id,
            limit=limit,
        )

    def get_action_events(
        self,
        action: str,
        *,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Return audit events for an action."""

        return self._repository.list_by_action(
            action,
            limit=limit,
        )