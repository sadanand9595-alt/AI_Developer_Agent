"""
Message repository for AI Command Center.

Provides persistence operations for conversation messages.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.message import Message, MessageRole


class MessageRepository:
    """Persistence operations for conversation messages."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        conversation_id: str,
        role: MessageRole,
        content: str,
        tool_name: str | None = None,
        metadata: dict | None = None,
    ) -> Message:
        """Create and persist a conversation message."""

        normalized_content = content.strip()

        if not normalized_content:
            raise ValueError(
                "Message content cannot be empty."
            )

        message = Message(
            conversation_id=conversation_id,
            role=role.value,
            content=normalized_content,
            tool_name=tool_name,
            metadata_json=metadata,
        )

        self._session.add(message)
        self._session.flush()

        return message

    def get_by_id(
        self,
        message_id: str,
    ) -> Message | None:
        """Return a message by ID."""

        statement = select(Message).where(
            Message.id == message_id
        )

        return self._session.scalar(statement)

    def list_by_conversation(
        self,
        conversation_id: str,
        *,
        limit: int | None = None,
    ) -> list[Message]:
        """Return messages in chronological order."""

        statement = (
            select(Message)
            .where(
                Message.conversation_id
                == conversation_id
            )
            .order_by(Message.created_at.asc())
        )

        if limit is not None:
            if limit < 1:
                raise ValueError(
                    "Limit must be greater than zero."
                )

            statement = statement.limit(limit)

        return list(
            self._session.scalars(statement).all()
        )

    def list_by_role(
        self,
        conversation_id: str,
        role: MessageRole,
    ) -> list[Message]:
        """Return messages matching a specific role."""

        statement = (
            select(Message)
            .where(
                Message.conversation_id
                == conversation_id,
                Message.role == role.value,
            )
            .order_by(Message.created_at.asc())
        )

        return list(
            self._session.scalars(statement).all()
        )

    def count(
        self,
        conversation_id: str,
    ) -> int:
        """Return the number of messages in a conversation."""

        statement = select(Message).where(
            Message.conversation_id
            == conversation_id
        )

        return len(
            self._session.scalars(statement).all()
        )