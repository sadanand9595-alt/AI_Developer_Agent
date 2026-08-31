"""
Message service for AI Command Center.

Contains business logic for creating and retrieving
conversation messages.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database.models.message import Message, MessageRole
from database.repositories.conversation_repository import (
    ConversationRepository,
)
from database.repositories.message_repository import (
    MessageRepository,
)


class MessageService:
    """Business operations for conversation messages."""

    def __init__(self, session: Session) -> None:
        self._repository = MessageRepository(session)
        self._conversation_repository = ConversationRepository(
            session
        )

    def add_user_message(
        self,
        *,
        conversation_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Add a user message."""

        return self._create_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            metadata=metadata,
        )

    def add_assistant_message(
        self,
        *,
        conversation_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Add an assistant message."""

        return self._create_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            metadata=metadata,
        )

    def add_tool_message(
        self,
        *,
        conversation_id: str,
        content: str,
        tool_name: str,
        metadata: dict | None = None,
    ) -> Message:
        """Add a tool execution message."""

        if not tool_name.strip():
            raise ValueError(
                "Tool name cannot be empty."
            )

        return self._create_message(
            conversation_id=conversation_id,
            role=MessageRole.TOOL,
            content=content,
            tool_name=tool_name,
            metadata=metadata,
        )

    def get_message(
        self,
        message_id: str,
    ) -> Message | None:
        """Get a message by ID."""

        return self._repository.get_by_id(message_id)

    def get_conversation_messages(
        self,
        conversation_id: str,
        *,
        limit: int | None = None,
    ) -> list[Message]:
        """Return messages in chronological order."""

        return self._repository.list_by_conversation(
            conversation_id,
            limit=limit,
        )

    def get_user_messages(
        self,
        conversation_id: str,
    ) -> list[Message]:
        """Return user messages."""

        return self._repository.list_by_role(
            conversation_id,
            MessageRole.USER,
        )

    def get_assistant_messages(
        self,
        conversation_id: str,
    ) -> list[Message]:
        """Return assistant messages."""

        return self._repository.list_by_role(
            conversation_id,
            MessageRole.ASSISTANT,
        )

    def count_messages(
        self,
        conversation_id: str,
    ) -> int:
        """Return the number of messages."""

        return self._repository.count(
            conversation_id
        )

    def _create_message(
        self,
        *,
        conversation_id: str,
        role: MessageRole,
        content: str,
        tool_name: str | None = None,
        metadata: dict | None = None,
    ) -> Message:
        """Create a message through the repository."""

        if not conversation_id.strip():
            raise ValueError(
                "Conversation ID cannot be empty."
            )

        if not content.strip():
            raise ValueError(
                "Message content cannot be empty."
            )

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
                "Cannot add a message to an archived "
                "conversation."
            )

        return self._repository.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_name=tool_name,
            metadata=metadata,
        )