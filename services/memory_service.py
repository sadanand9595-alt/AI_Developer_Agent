"""
Memory service for AI Command Center.

Contains business logic for creating, retrieving, updating,
accessing, and deactivating long-term memories.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.models.memory import Memory
from database.repositories.conversation_repository import (
    ConversationRepository,
)
from database.repositories.memory_repository import (
    MemoryRepository,
)


class MemoryService:
    """Business operations for long-term memories."""

    def __init__(self, session: Session) -> None:
        self._repository = MemoryRepository(session)
        self._conversation_repository = ConversationRepository(
            session
        )

    def create_memory(
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
        """Create a new long-term memory."""

        normalized_content = content.strip()

        if not normalized_content:
            raise ValueError(
                "Memory content cannot be empty."
            )

        if conversation_id is not None:
            conversation = (
                self._conversation_repository.get_by_id(
                    conversation_id
                )
            )

            if conversation is None:
                raise ValueError(
                    "Conversation not found."
                )

            if conversation.is_archived:
                raise ValueError(
                    "Cannot add a memory to an archived "
                    "conversation."
                )

        return self._repository.create(
            user_id=user_id,
            content=normalized_content,
            memory_type=memory_type,
            conversation_id=conversation_id,
            source=source,
            metadata=metadata,
            importance=importance,
        )

    def get_memory(
        self,
        memory_id: str,
    ) -> Memory | None:
        """Get a memory by ID."""

        return self._repository.get_by_id(memory_id)

    def get_user_memories(
        self,
        user_id: str,
        *,
        memory_type: str | None = None,
        active_only: bool = True,
    ) -> list[Memory]:
        """Return memories belonging to a user."""

        return self._repository.list_by_user(
            user_id,
            memory_type=memory_type,
            active_only=active_only,
        )

    def access_memory(
        self,
        memory_id: str,
    ) -> Memory:
        """Mark a memory as accessed."""

        memory = self._get_required_memory(
            memory_id
        )

        if not memory.is_active:
            raise ValueError(
                "Cannot access an inactive memory."
            )

        return self._repository.mark_accessed(
            memory
        )

    def update_importance(
        self,
        memory_id: str,
        importance: float,
    ) -> Memory:
        """Update memory importance."""

        memory = self._get_required_memory(
            memory_id
        )

        return self._repository.update_importance(
            memory,
            importance,
        )

    def deactivate_memory(
        self,
        memory_id: str,
    ) -> Memory:
        """Deactivate a memory."""

        memory = self._get_required_memory(
            memory_id
        )

        return self._repository.deactivate(
            memory
        )

    def _get_required_memory(
        self,
        memory_id: str,
    ) -> Memory:
        """Return a memory or raise a controlled error."""

        memory = self._repository.get_by_id(
            memory_id
        )

        if memory is None:
            raise ValueError(
                "Memory not found."
            )

        return memory