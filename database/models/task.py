"""
Task database model for AI Command Center.

A task represents a unit of work requested by a user and
executed by the AI planning/agent system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.types import TaskStatus
from database.base import Base


class Task(Base):
    """Persistent AI task."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    conversation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    parent_task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        default=TaskStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    priority: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    plan_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    result_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    retry_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"Task("
            f"id={self.id!r}, "
            f"title={self.title!r}, "
            f"status={self.status!r}"
            f")"
        )

    def mark_started(self) -> None:
        """Mark the task as running."""

        now = datetime.now(timezone.utc)

        self.status = TaskStatus.RUNNING.value
        self.started_at = now
        self.updated_at = now

    def mark_completed(
        self,
        result: dict | None = None,
    ) -> None:
        """Mark the task as completed."""

        now = datetime.now(timezone.utc)

        self.status = TaskStatus.COMPLETED.value
        self.result_json = result
        self.completed_at = now
        self.updated_at = now

    def mark_failed(
        self,
        error: dict | None = None,
    ) -> None:
        """Mark the task as failed."""

        self.status = TaskStatus.FAILED.value
        self.error_json = error
        self.updated_at = datetime.now(timezone.utc)

    def increment_retry(self) -> None:
        """Increase the retry counter."""

        self.retry_count += 1
        self.updated_at = datetime.now(timezone.utc)