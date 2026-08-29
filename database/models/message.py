"""
Conversation message database model for AI Command Center.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class MessageRole(StrEnum):
    """Role of the message sender."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(Base):
    """Persistent message belonging to a conversation."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tool_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"Message("
            f"id={self.id!r}, "
            f"conversation_id={self.conversation_id!r}, "
            f"role={self.role!r}"
            f")"
        )