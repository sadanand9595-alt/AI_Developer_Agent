from uuid import uuid4

from database.models.message import MessageRole
from database.repositories.conversation_repository import (
    ConversationRepository,
)
from database.repositories.message_repository import (
    MessageRepository,
)
from database.repositories.user_repository import UserRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        user_repository = UserRepository(session)

        user = user_repository.create(
            email=f"message-{uuid4()}@example.com",
            name="Message Test User",
        )

        conversation_repository = ConversationRepository(
            session
        )

        conversation = conversation_repository.create(
            user_id=user.id,
            title="Message Test Conversation",
        )

        repository = MessageRepository(session)

        user_message = repository.create(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Hello AI",
        )

        assistant_message = repository.create(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Hello! How can I help?",
        )

        tool_message = repository.create(
            conversation_id=conversation.id,
            role=MessageRole.TOOL,
            content="Tool execution completed.",
            tool_name="test_tool",
            metadata={
                "success": True,
            },
        )

        print(
            "USER MESSAGE:",
            user_message.id,
            user_message.role,
        )

        print(
            "ASSISTANT MESSAGE:",
            assistant_message.id,
            assistant_message.role,
        )

        print(
            "TOOL MESSAGE:",
            tool_message.id,
            tool_message.role,
        )

        found = repository.get_by_id(
            assistant_message.id
        )

        if found is None:
            raise RuntimeError(
                "Message could not be read."
            )

        print("READ:", found.content)

        messages = repository.list_by_conversation(
            conversation.id
        )

        print(
            "TOTAL MESSAGES:",
            len(messages),
        )

        user_messages = repository.list_by_role(
            conversation.id,
            MessageRole.USER,
        )

        print(
            "USER MESSAGES:",
            len(user_messages),
        )

        print(
            "COUNT:",
            repository.count(conversation.id),
        )


if __name__ == "__main__":
    main()