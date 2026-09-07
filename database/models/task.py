"""
Task database model for AI Command Center.

A task represents a unit of work requested by a user and
executed by the AI planning/agent system.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.types import TaskStatus
from database.base import Base


class Task(Base):
    """Persistent AI task."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    conversation_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    parent_task_id: Mapped[str | None] = mapped_column(
        String(255),
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

    execution_id: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )

    lease_owner_id: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )

    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    def mark_started(
        self,
        execution_id: str | None = None,
        *,
        lease_owner_id: str | None = None,
        lease_ttl_seconds: int = 300,
    ) -> None:
        """Mark the task as running."""

        if self.status in (
            TaskStatus.RUNNING.value,
            TaskStatus.COMPLETED.value,
        ):
            raise ValueError(
                "Cannot start a task with status "
                f"{self.status!r}."
            )

        now = datetime.now(timezone.utc)

        normalized_execution_id = (
            execution_id.strip()
            if isinstance(execution_id, str)
            else self.execution_id
        )

        if normalized_execution_id is None:
            normalized_execution_id = str(uuid4())

        normalized_lease_owner_id = (
            lease_owner_id.strip()
            if isinstance(lease_owner_id, str)
            else self.lease_owner_id
        )
        if normalized_lease_owner_id is None:
            normalized_lease_owner_id = normalized_execution_id
        if normalized_lease_owner_id != normalized_execution_id:
            raise ValueError(
                "lease_owner_id must match execution_id for task start."
            )

        self.status = TaskStatus.RUNNING.value
        self.started_at = now
        self.updated_at = now
        self.execution_id = normalized_execution_id
        self.lease_owner_id = normalized_lease_owner_id
        self.last_heartbeat_at = now
        self.lease_expires_at = now + timedelta(
            seconds=max(0, int(lease_ttl_seconds))
        )

    def mark_completed(
        self,
        result: dict | None = None,
    ) -> None:
        """Mark the task as completed."""

        if self.status in (
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
        ):
            raise ValueError(
                "Cannot complete a task with status "
                f"{self.status!r}."
            )

        now = datetime.now(timezone.utc)

        self.status = TaskStatus.COMPLETED.value
        self.result_json = result
        self.error_json = None
        self.completed_at = now
        self.updated_at = now
        self.lease_owner_id = None
        self.lease_expires_at = None
        self.last_heartbeat_at = None

    def mark_failed(
        self,
        error: dict | None = None,
    ) -> None:
        """Mark the task as failed."""

        if self.status in (
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
        ):
            raise ValueError(
                "Cannot fail a task with status "
                f"{self.status!r}."
            )

        self.status = TaskStatus.FAILED.value
        self.result_json = None
        self.error_json = error
        self.updated_at = datetime.now(timezone.utc)
        self.lease_owner_id = None
        self.lease_expires_at = None
        self.last_heartbeat_at = None

    def increment_retry(self) -> None:
        """Increase the retry counter."""

        self.retry_count += 1
        self.updated_at = datetime.now(timezone.utc)