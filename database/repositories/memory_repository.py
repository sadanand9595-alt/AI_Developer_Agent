"""
Memory repository for AI Command Center.

Provides persistence operations for long-term AI memory records.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.memory import Memory


class MemoryRepository:
    """Persistence operations for memory records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        user_id: str,
        content: str,
        memory_type: str,
        conversation_id: str | None = None,
        source: str | None = None,
        metadata: dict | None = None,
        importance: float = 0.5,
    ) -> Memory:
        """Create and persist a memory record."""

        normalized_content = content.strip()
        normalized_type = memory_type.strip()

        if not normalized_content:
            raise ValueError(
                "Memory content cannot be empty."
            )

        if not normalized_type:
            raise ValueError(
                "Memory type cannot be empty."
            )

        if not 0.0 <= importance <= 1.0:
            raise ValueError(
                "Memory importance must be between 0.0 and 1.0."
            )

        memory = Memory(
            user_id=user_id,
            conversation_id=conversation_id,
            memory_type=normalized_type,
            content=normalized_content,
            source=source,
            metadata_json=metadata,
            importance=importance,
            is_active=True,
        )

        self._session.add(memory)
        self._session.flush()

        return memory

    def get_by_id(
        self,
        memory_id: str,
    ) -> Memory | None:
        """Return a memory by ID."""

        statement = select(Memory).where(
            Memory.id == memory_id
        )

        return self._session.scalar(statement)

    def list_by_user(
        self,
        user_id: str,
        *,
        memory_type: str | None = None,
        active_only: bool = True,
    ) -> list[Memory]:
        """Return memories belonging to a user."""

        statement = select(Memory).where(
            Memory.user_id == user_id
        )

        if active_only:
            statement = statement.where(
                Memory.is_active.is_(True)
            )

        if memory_type:
            statement = statement.where(
                Memory.memory_type == memory_type.strip()
            )

        statement = statement.order_by(
            Memory.importance.desc(),
            Memory.updated_at.desc(),
        )

        return list(
            self._session.scalars(statement).all()
        )

    def mark_accessed(
        self,
        memory: Memory,
    ) -> Memory:
        """Record a memory access."""

        memory.mark_accessed()
        self._session.flush()

        return memory

    def deactivate(
        self,
        memory: Memory,
    ) -> Memory:
        """Deactivate a memory."""

        memory.deactivate()
        self._session.flush()

        return memory

    def update_importance(
        self,
        memory: Memory,
        importance: float,
    ) -> Memory:
        """Update the importance score of a memory."""

        if not 0.0 <= importance <= 1.0:
            raise ValueError(
                "Memory importance must be between 0.0 and 1.0."
            )

        memory.importance = importance
        memory.updated_at = datetime.now(timezone.utc)

        self._session.flush()

        return memory