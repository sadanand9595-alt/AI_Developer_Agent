from uuid import uuid4

from database.repositories.conversation_repository import (
    ConversationRepository,
)
from database.repositories.user_repository import UserRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        user_repository = UserRepository(session)

        user = user_repository.create(
            email=f"conversation-{uuid4()}@example.com",
            name="Conversation Test User",
        )

        repository = ConversationRepository(session)

        conversation = repository.create(
            user_id=user.id,
            title="Test Conversation",
            system_context="Testing conversation persistence.",
        )

        print(
            "CREATED:",
            conversation.id,
            conversation.title,
        )

        found = repository.get_by_id(
            conversation.id
        )

        if found is None:
            raise RuntimeError(
                "Conversation could not be read."
            )

        print("READ:", found.title)

        repository.rename(
            found,
            "Updated Test Conversation",
        )

        print("RENAMED:", found.title)

        conversations = repository.list_by_user(
            user.id
        )

        print(
            "USER CONVERSATIONS:",
            len(conversations),
        )

        repository.archive(found)

        print(
            "ARCHIVED:",
            found.is_archived,
        )


if __name__ == "__main__":
    main()