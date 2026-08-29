"""
AI Agent database model for AI Command Center.

Stores registered agents, their capabilities, configuration,
and operational status.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.types import AgentStatus
from database.base import Base


class Agent(Base):
    """Persistent registered AI agent."""

    __tablename__ = "agents"

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

    agent_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    model_provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    capabilities: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    configuration: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        default=AgentStatus.IDLE.value,
        nullable=False,
        index=True,
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    max_iterations: Mapped[int] = mapped_column(
        default=10,
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

    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"Agent("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"agent_type={self.agent_type!r}, "
            f"status={self.status!r}"
            f")"
        )

    def activate(self) -> None:
        """Enable the agent."""

        self.is_enabled = True
        self.status = AgentStatus.IDLE.value
        self.updated_at = datetime.now(timezone.utc)

    def disable(self) -> None:
        """Disable the agent."""

        self.is_enabled = False
        self.status = AgentStatus.DISABLED.value
        self.updated_at = datetime.now(timezone.utc)

    def mark_active(self) -> None:
        """Record agent activity."""

        now = datetime.now(timezone.utc)

        self.status = AgentStatus.RUNNING.value
        self.last_active_at = now
        self.updated_at = now