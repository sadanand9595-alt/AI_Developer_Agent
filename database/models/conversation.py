"""
Conversation database model for AI Command Center.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Conversation(Base):
    """Persistent conversation between a user and the AI system."""

    __tablename__ = "conversations"

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

    title: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    system_context: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_archived: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"Conversation("
            f"id={self.id!r}, "
            f"user_id={self.user_id!r}, "
            f"title={self.title!r}"
            f")"
        )

    def archive(self) -> None:
        """Archive the conversation."""

        self.is_archived = True
        self.updated_at = datetime.now(timezone.utc)

    def rename(self, title: str) -> None:
        """Update the conversation title."""

        cleaned_title = title.strip()

        if not cleaned_title:
            raise ValueError(
                "Conversation title cannot be empty."
            )

        self.title = cleaned_title
        self.updated_at = datetime.now(timezone.utc)