from uuid import uuid4

from core.types import ToolRiskLevel
from database.models.message import MessageRole
from database.repositories.agent_repository import AgentRepository
from database.repositories.audit_repository import AuditRepository
from database.repositories.approval_repository import ApprovalRepository
from database.repositories.conversation_repository import (
    ConversationRepository,
)
from database.repositories.memory_repository import MemoryRepository
from database.repositories.message_repository import (
    MessageRepository,
)
from database.repositories.task_repository import TaskRepository
from database.repositories.tool_repository import ToolRepository
from database.repositories.user_repository import UserRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        # 1. USER
        user_repo = UserRepository(session)

        user = user_repo.create(
            email=f"integration-{uuid4()}@example.com",
            name="Integration Test User",
            password_hash="test-hash-not-used",
        )

        print("USER: PASS")

        # 2. CONVERSATION
        conversation_repo = ConversationRepository(
            session
        )

        conversation = conversation_repo.create(
            user_id=user.id,
            title="Integration Test Conversation",
        )

        print("CONVERSATION: PASS")

        # 3. MESSAGE
        message_repo = MessageRepository(session)

        message_repo.create(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Run integration test.",
        )

        message_repo.create(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Integration test started.",
        )

        print("MESSAGE: PASS")

        # 4. TASK
        task_repo = TaskRepository(session)

        task = task_repo.create(
            user_id=user.id,
            conversation_id=conversation.id,
            title="Integration Test Task",
            description="Testing repository integration.",
            priority=10,
        )

        task_repo.mark_started(task)

        print("TASK: PASS")

        # 5. AGENT
        agent_repo = AgentRepository(session)

        agent = agent_repo.create(
            name=f"Integration Agent {uuid4()}",
            agent_type="coding",
            model_provider="local",
            model_name="test-model",
            capabilities=[
                "coding",
                "testing",
            ],
        )

        agent_repo.mark_active(agent)

        print("AGENT: PASS")

        # 6. TOOL
        tool_repo = ToolRepository(session)

        tool = tool_repo.create(
            name=f"Integration Tool {uuid4()}",
            tool_type="filesystem",
            risk_level=ToolRiskLevel.MEDIUM,
            permissions=["read", "write"],
            requires_approval=True,
        )

        tool_repo.mark_used(tool)

        print("TOOL: PASS")

        # 7. APPROVAL
        approval_repo = ApprovalRepository(session)

        approval = approval_repo.create(
            user_id=user.id,
            task_id=task.id,
            tool_id=tool.id,
            action="filesystem_write",
            reason="Integration test.",
            requested_operation="Write test file.",
        )

        approval_repo.approve(
            approval,
            reviewer_id=user.id,
            comment="Approved for integration test.",
        )

        print("APPROVAL: PASS")

        # 8. MEMORY
        memory_repo = MemoryRepository(session)

        memory_repo.create(
            user_id=user.id,
            conversation_id=conversation.id,
            content="Integration test memory.",
            memory_type="test",
            importance=0.8,
        )

        print("MEMORY: PASS")

        # 9. AUDIT
        audit_repo = AuditRepository(session)

        audit_repo.create(
            user_id=user.id,
            task_id=task.id,
            agent_id=agent.id,
            tool_id=tool.id,
            action="integration_test",
            category="testing",
            status="success",
            message="Repository integration completed.",
        )

        print("AUDIT: PASS")

        # 10. COMPLETE TASK
        task_repo.mark_completed(
            task,
            {
                "status": "integration_test_passed",
            },
        )

        print("TASK COMPLETION: PASS")

        print()
        print("=" * 50)
        print("ALL REPOSITORY INTEGRATION TESTS PASSED")
        print("=" * 50)


if __name__ == "__main__":
    main()