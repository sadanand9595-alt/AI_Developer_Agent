"""
Human approval database model for AI Command Center.

Stores approval requests created when an agent or tool wants
to perform an action that requires human authorization.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.types import ApprovalStatus
from database.base import Base


class ApprovalRequest(Base):
    """Persistent human approval request."""

    __tablename__ = "approval_requests"

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

    execution_id: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )

    plan_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )

    step_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )

    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
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
        String(100),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    requested_operation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    request_payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        default=ApprovalStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reviewed_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewer_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"ApprovalRequest("
            f"id={self.id!r}, "
            f"action={self.action!r}, "
            f"status={self.status!r}"
            f")"
        )

    def _is_expired(self) -> bool:
        """Return whether the approval window has passed."""

        return (
            self.expires_at is not None
            and self.expires_at
            <= datetime.now(timezone.utc)
        )

    def approve(
        self,
        reviewer_id: str,
        comment: str | None = None,
    ) -> None:
        """Approve the requested operation."""

        if self.status != ApprovalStatus.PENDING.value:
            raise ValueError(
                "Only pending approval requests can be approved."
            )

        # A pending request past its expires_at must not be
        # approvable: the approval window has already lapsed,
        # so this authorizes the gated action after the human
        # approval boundary was meant to have closed.
        if self._is_expired():
            self.status = ApprovalStatus.EXPIRED.value
            self.reviewed_at = datetime.now(timezone.utc)

            raise ValueError(
                "Approval request has expired and can no "
                "longer be approved."
            )

        self.status = ApprovalStatus.APPROVED.value
        self.reviewed_by = reviewer_id
        self.reviewer_comment = comment
        self.reviewed_at = datetime.now(timezone.utc)

    def reject(
        self,
        reviewer_id: str,
        comment: str | None = None,
    ) -> None:
        """Reject the requested operation."""

        if self.status != ApprovalStatus.PENDING.value:
            raise ValueError(
                "Only pending approval requests can be rejected."
            )

        self.status = ApprovalStatus.REJECTED.value
        self.reviewed_by = reviewer_id
        self.reviewer_comment = comment
        self.reviewed_at = datetime.now(timezone.utc)

    def expire(self) -> None:
        """Mark a pending approval request as expired."""

        if self.status != ApprovalStatus.PENDING.value:
            return

        self.status = ApprovalStatus.EXPIRED.value
        self.reviewed_at = datetime.now(timezone.utc)