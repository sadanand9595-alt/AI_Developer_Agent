"""
Conversation repository for AI Command Center.

Provides persistence operations for conversations.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.conversation import Conversation


class ConversationRepository:
    """Persistence operations for conversations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        user_id: str,
        title: str | None = None,
        system_context: str | None = None,
    ) -> Conversation:
        """Create and persist a new conversation."""

        normalized_title = (
            title.strip()
            if title is not None
            else None
        )

        if normalized_title == "":
            normalized_title = None

        conversation = Conversation(
            user_id=user_id,
            title=normalized_title,
            system_context=system_context,
        )

        self._session.add(conversation)
        self._session.flush()

        return conversation

    def get_by_id(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        """Return a conversation by ID."""

        statement = select(Conversation).where(
            Conversation.id == conversation_id
        )

        return self._session.scalar(statement)

    def list_by_user(
        self,
        user_id: str,
        *,
        include_archived: bool = False,
    ) -> list[Conversation]:
        """Return conversations belonging to a user."""

        statement = select(Conversation).where(
            Conversation.user_id == user_id
        )

        if not include_archived:
            statement = statement.where(
                Conversation.is_archived.is_(False)
            )

        statement = statement.order_by(
            Conversation.updated_at.desc()
        )

        return list(
            self._session.scalars(statement).all()
        )

    def rename(
        self,
        conversation: Conversation,
        title: str,
    ) -> Conversation:
        """Rename a conversation."""

        conversation.rename(title)
        self._session.flush()

        return conversation

    def archive(
        self,
        conversation: Conversation,
    ) -> Conversation:
        """Archive a conversation."""

        conversation.archive()
        self._session.flush()

        return conversation