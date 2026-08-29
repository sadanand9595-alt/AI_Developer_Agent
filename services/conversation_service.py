"""
Conversation service for AI Command Center.

Contains business logic for creating, retrieving, renaming,
listing, and archiving conversations.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.models.conversation import Conversation
from database.repositories.conversation_repository import (
    ConversationRepository,
)


class ConversationService:
    """Business operations for conversations."""

    def __init__(self, session: Session) -> None:
        self._repository = ConversationRepository(session)

    def create_conversation(
        self,
        *,
        user_id: str,
        title: str | None = None,
        system_context: str | None = None,
    ) -> Conversation:
        """Create a new conversation."""

        return self._repository.create(
            user_id=user_id,
            title=title,
            system_context=system_context,
        )

    def get_conversation(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        """Get a conversation by ID."""

        return self._repository.get_by_id(
            conversation_id
        )

    def list_user_conversations(
        self,
        user_id: str,
        *,
        include_archived: bool = False,
    ) -> list[Conversation]:
        """List conversations belonging to a user."""

        return self._repository.list_by_user(
            user_id,
            include_archived=include_archived,
        )

    def rename_conversation(
        self,
        conversation_id: str,
        title: str,
    ) -> Conversation:
        """Rename a conversation."""

        conversation = self._repository.get_by_id(
            conversation_id
        )

        if conversation is None:
            raise ValueError(
                "Conversation not found."
            )

        return self._repository.rename(
            conversation,
            title,
        )

    def archive_conversation(
        self,
        conversation_id: str,
    ) -> Conversation:
        """Archive a conversation."""

        conversation = self._repository.get_by_id(
            conversation_id
        )

        if conversation is None:
            raise ValueError(
                "Conversation not found."
            )

        return self._repository.archive(
            conversation
        )