"""
Tool database model for AI Command Center.

Stores registered tools, their capabilities, risk levels,
configuration, and operational state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.types import ToolRiskLevel
from database.base import Base


class Tool(Base):
    """Persistent registered AI tool."""

    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    name: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tool_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        default="1.0.0",
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(40),
        default=ToolRiskLevel.READ_ONLY.value,
        nullable=False,
        index=True,
    )

    input_schema: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    output_schema: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    configuration: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    permissions: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    requires_approval: Mapped[bool] = mapped_column(
        Boolean,
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

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"Tool("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"tool_type={self.tool_type!r}, "
            f"risk_level={self.risk_level!r}"
            f")"
        )

    def enable(self) -> None:
        """Enable the tool."""

        self.is_enabled = True
        self.updated_at = datetime.now(timezone.utc)

    def disable(self) -> None:
        """Disable the tool."""

        self.is_enabled = False
        self.updated_at = datetime.now(timezone.utc)

    def mark_used(self) -> None:
        """Record the latest tool usage."""

        now = datetime.now(timezone.utc)
        self.last_used_at = now
        self.updated_at = now