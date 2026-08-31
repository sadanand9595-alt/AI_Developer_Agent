from uuid import uuid4

from database.session import session_scope
from services.conversation_service import ConversationService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"conversation-service-{uuid4()}@example.com",
            name="Conversation Service Test User",
            password_hash="test-hash-not-used",
        )

        conversation_service = ConversationService(
            session
        )

        conversation = (
            conversation_service.create_conversation(
                user_id=user.id,
                title="Test Conversation",
                system_context="Testing ConversationService.",
            )
        )

        print(
            "CREATED:",
            conversation.id,
            conversation.title,
        )

        found = (
            conversation_service.get_conversation(
                conversation.id
            )
        )

        if found is None:
            raise RuntimeError(
                "Conversation could not be retrieved."
            )

        print("READ:", found.title)

        updated = (
            conversation_service.rename_conversation(
                conversation.id,
                "Updated Test Conversation",
            )
        )

        print("RENAMED:", updated.title)

        conversations = (
            conversation_service.list_user_conversations(
                user.id
            )
        )

        print(
            "USER CONVERSATIONS:",
            len(conversations),
        )

        archived = (
            conversation_service.archive_conversation(
                conversation.id
            )
        )

        print(
            "ARCHIVED:",
            archived.is_archived,
        )

        all_conversations = (
            conversation_service.list_user_conversations(
                user.id,
                include_archived=True,
            )
        )

        print(
            "INCLUDING ARCHIVED:",
            len(all_conversations),
        )


if __name__ == "__main__":
    main()