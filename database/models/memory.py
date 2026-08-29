"""
Memory database model for AI Command Center.

Stores persistent memory records and their metadata.
Actual vector embeddings can be stored in a dedicated vector
store later; this model keeps the authoritative metadata.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Memory(Base):
    """Persistent AI memory record."""

    __tablename__ = "memories"

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

    memory_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    importance: Mapped[float] = mapped_column(
        default=0.5,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
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

    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"Memory("
            f"id={self.id!r}, "
            f"user_id={self.user_id!r}, "
            f"memory_type={self.memory_type!r}"
            f")"
        )

    def mark_accessed(self) -> None:
        """Record the latest memory access."""

        self.last_accessed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivate this memory record."""

        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)