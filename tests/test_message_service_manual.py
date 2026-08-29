from uuid import uuid4

from database.session import session_scope
from services.conversation_service import ConversationService
from services.message_service import MessageService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"message-service-{uuid4()}@example.com",
            name="Message Service Test User",
        )

        conversation_service = ConversationService(
            session
        )

        conversation = (
            conversation_service.create_conversation(
                user_id=user.id,
                title="Message Service Test",
            )
        )

        message_service = MessageService(session)

        user_message = (
            message_service.add_user_message(
                conversation_id=conversation.id,
                content="Hello AI",
            )
        )

        print(
            "USER:",
            user_message.role,
            user_message.content,
        )

        assistant_message = (
            message_service.add_assistant_message(
                conversation_id=conversation.id,
                content="Hello! How can I help?",
            )
        )

        print(
            "ASSISTANT:",
            assistant_message.role,
            assistant_message.content,
        )

        tool_message = (
            message_service.add_tool_message(
                conversation_id=conversation.id,
                content="File listing completed.",
                tool_name="filesystem",
                metadata={
                    "success": True,
                },
            )
        )

        print(
            "TOOL:",
            tool_message.role,
            tool_message.tool_name,
        )

        found = message_service.get_message(
            assistant_message.id
        )

        if found is None:
            raise RuntimeError(
                "Message could not be retrieved."
            )

        print("READ:", found.content)

        messages = (
            message_service.get_conversation_messages(
                conversation.id
            )
        )

        print(
            "TOTAL MESSAGES:",
            len(messages),
        )

        user_messages = (
            message_service.get_user_messages(
                conversation.id
            )
        )

        print(
            "USER MESSAGES:",
            len(user_messages),
        )

        assistant_messages = (
            message_service.get_assistant_messages(
                conversation.id
            )
        )

        print(
            "ASSISTANT MESSAGES:",
            len(assistant_messages),
        )

        print(
            "COUNT:",
            message_service.count_messages(
                conversation.id
            ),
        )


if __name__ == "__main__":
    main()