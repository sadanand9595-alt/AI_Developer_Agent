from uuid import uuid4

from database.session import session_scope
from services.conversation_service import ConversationService
from services.memory_service import MemoryService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"memory-service-{uuid4()}@example.com",
            name="Memory Service Test User",
        )

        memory_service = MemoryService(session)

        memory = memory_service.create_memory(
            user_id=user.id,
            content="User prefers production-ready architecture.",
            memory_type="preference",
            source="test",
            metadata={
                "category": "development",
            },
            importance=0.8,
        )

        print("CREATED:", memory.id)
        print("TYPE:", memory.memory_type)
        print("IMPORTANCE:", memory.importance)

        found = memory_service.get_memory(memory.id)

        if found is None:
            raise RuntimeError("Memory could not be retrieved.")

        print("READ:", found.content)

        accessed = memory_service.access_memory(memory.id)

        print("ACCESSED:", accessed.last_accessed_at is not None)

        updated = memory_service.update_importance(
            memory.id,
            0.95,
        )

        print("UPDATED IMPORTANCE:", updated.importance)

        memories = memory_service.get_user_memories(user.id)

        print("USER MEMORIES:", len(memories))

        deactivated = memory_service.deactivate_memory(memory.id)

        print("ACTIVE:", deactivated.is_active)

        # -------------------------------------------------
        # MEMORY <-> CONVERSATION PARENT LIFECYCLE
        # -------------------------------------------------
        #
        # A memory created without a conversation_id must be
        # unaffected. A memory created against a nonexistent or
        # archived conversation must be rejected with a clean
        # ValueError, not an uncaught database IntegrityError.
        # -------------------------------------------------

        no_conversation_memory = memory_service.create_memory(
            user_id=user.id,
            content="Memory without a conversation.",
            memory_type="fact",
        )

        if no_conversation_memory.conversation_id is not None:
            raise RuntimeError(
                "Memory without a conversation_id should "
                "not gain one."
            )

        print("MEMORY WITHOUT CONVERSATION: PASS")

        conversation_service = ConversationService(session)

        conversation = (
            conversation_service.create_conversation(
                user_id=user.id,
                title="Memory Lifecycle Test",
            )
        )

        linked_memory = memory_service.create_memory(
            user_id=user.id,
            content="Memory linked to a live conversation.",
            memory_type="fact",
            conversation_id=conversation.id,
        )

        if linked_memory.conversation_id != conversation.id:
            raise RuntimeError(
                "Memory should be linked to the conversation."
            )

        print("MEMORY WITH VALID CONVERSATION: PASS")

        try:
            memory_service.create_memory(
                user_id=user.id,
                content="Should not be created.",
                memory_type="fact",
                conversation_id="nonexistent-conversation-id",
            )
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Memory for a nonexistent conversation should "
                "be rejected."
            )

        print("MISSING CONVERSATION PROTECTION: PASS")

        conversation_service.archive_conversation(
            conversation.id
        )

        try:
            memory_service.create_memory(
                user_id=user.id,
                content="Should not be added after archive.",
                memory_type="fact",
                conversation_id=conversation.id,
            )
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Memory should not be addable to an archived "
                "conversation."
            )

        print("ARCHIVED CONVERSATION PROTECTION: PASS")


if __name__ == "__main__":
    main()
