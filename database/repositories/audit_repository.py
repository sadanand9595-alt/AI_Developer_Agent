"""
Audit repository for AI Command Center.

Provides persistence operations for immutable audit records.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.audit import AuditLog


class AuditRepository:
    """Persistence operations for audit logs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
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
        """Create and persist an audit record."""

        normalized_action = action.strip()
        normalized_category = category.strip()
        normalized_status = status.strip()

        if not normalized_action:
            raise ValueError(
                "Audit action cannot be empty."
            )

        if not normalized_category:
            raise ValueError(
                "Audit category cannot be empty."
            )

        if not normalized_status:
            raise ValueError(
                "Audit status cannot be empty."
            )

        audit = AuditLog(
            user_id=user_id,
            task_id=task_id,
            agent_id=agent_id,
            tool_id=tool_id,
            action=normalized_action,
            category=normalized_category,
            status=normalized_status,
            message=message,
            metadata_json=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self._session.add(audit)
        self._session.flush()

        return audit

    def get_by_id(
        self,
        audit_id: str,
    ) -> AuditLog | None:
        """Return an audit record by ID."""

        statement = select(AuditLog).where(
            AuditLog.id == audit_id
        )

        return self._session.scalar(statement)

    def list_by_user(
        self,
        user_id: str,
        *,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Return recent audit records for a user."""

        if limit < 1:
            raise ValueError(
                "Limit must be greater than zero."
            )

        statement = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        return list(
            self._session.scalars(statement).all()
        )

    def list_by_task(
        self,
        task_id: str,
        *,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Return audit records for a task."""

        if limit < 1:
            raise ValueError(
                "Limit must be greater than zero."
            )

        statement = (
            select(AuditLog)
            .where(AuditLog.task_id == task_id)
            .order_by(AuditLog.created_at.asc())
            .limit(limit)
        )

        return list(
            self._session.scalars(statement).all()
        )

    def list_by_action(
        self,
        action: str,
        *,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Return audit records for a specific action."""

        if limit < 1:
            raise ValueError(
                "Limit must be greater than zero."
            )

        statement = (
            select(AuditLog)
            .where(AuditLog.action == action.strip())
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        return list(
            self._session.scalars(statement).all()
        )