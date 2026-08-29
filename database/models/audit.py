"""
Audit log database model for AI Command Center.

Stores an immutable record of important user, agent, tool,
security, approval, and execution actions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class AuditLog(Base):
    """Persistent audit record."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    tool_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tools.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"AuditLog("
            f"id={self.id!r}, "
            f"action={self.action!r}, "
            f"status={self.status!r}"
            f")"
        )