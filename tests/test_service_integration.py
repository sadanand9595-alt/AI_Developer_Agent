from uuid import uuid4

from core.types import ToolRiskLevel
from database.models.message import MessageRole
from database.session import session_scope

from services.agent_service import AgentService
from services.approval_service import ApprovalService
from services.audit_service import AuditService
from services.conversation_service import ConversationService
from services.memory_service import MemoryService
from services.message_service import MessageService
from services.task_service import TaskService
from services.tool_service import ToolService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        # 1. USER
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"service-integration-{uuid4()}@example.com",
            name="Service Integration User",
            password_hash="test-hash-not-used",
        )

        print("USER SERVICE: PASS")

        # 2. CONVERSATION
        conversation_service = ConversationService(
            session
        )

        conversation = (
            conversation_service.create_conversation(
                user_id=user.id,
                title="Service Integration Conversation",
            )
        )

        print("CONVERSATION SERVICE: PASS")

        # 3. MESSAGE
        message_service = MessageService(session)

        message_service.add_user_message(
            conversation_id=conversation.id,
            content="Run service integration test.",
        )

        message_service.add_assistant_message(
            conversation_id=conversation.id,
            content="Service integration test started.",
        )

        message_service.add_tool_message(
            conversation_id=conversation.id,
            content="Tool execution completed.",
            tool_name="integration_tool",
        )

        print("MESSAGE SERVICE: PASS")

        # 4. TASK
        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user.id,
            conversation_id=conversation.id,
            title="Service Integration Task",
            description="Testing complete service layer.",
            priority=10,
        )

        task_service.start_task(task.id)

        print("TASK START: PASS")

        # 5. AGENT
        agent_service = AgentService(session)

        agent = agent_service.register_agent(
            name=f"Integration Agent {uuid4()}",
            agent_type="coding",
            model_provider="local",
            model_name="test-model",
            capabilities=[
                "coding",
                "testing",
            ],
        )

        agent_service.mark_agent_active(agent.id)

        print("AGENT SERVICE: PASS")

        # 6. TOOL
        tool_service = ToolService(session)

        tool = tool_service.register_tool(
            name=f"Integration Tool {uuid4()}",
            tool_type="filesystem",
            risk_level=ToolRiskLevel.MEDIUM,
            permissions=[
                "read",
                "write",
            ],
            requires_approval=False,
        )

        tool_service.mark_tool_used(tool.id)

        print("TOOL SERVICE: PASS")
        print(
            "TOOL APPROVAL:",
            tool_service.requires_approval(tool.id),
        )

        # 7. APPROVAL
        approval_service = ApprovalService(session)

        approval = approval_service.request_approval(
            user_id=user.id,
            task_id=task.id,
            tool_id=tool.id,
            action="filesystem_write",
            reason="Service integration test.",
            requested_operation="Write integration test file.",
        )

        print("APPROVAL CREATED: PASS")

        approval_service.approve(
            approval.id,
            reviewer_id=user.id,
            comment="Approved for integration testing.",
        )

        print("APPROVAL WORKFLOW: PASS")

        # 8. MEMORY
        memory_service = MemoryService(session)

        memory = memory_service.create_memory(
            user_id=user.id,
            conversation_id=conversation.id,
            content="Service integration test memory.",
            memory_type="test",
            source="integration",
            importance=0.8,
        )

        memory_service.access_memory(memory.id)

        print("MEMORY SERVICE: PASS")

        # 9. AUDIT
        audit_service = AuditService(session)

        audit = audit_service.record_event(
            user_id=user.id,
            task_id=task.id,
            agent_id=agent.id,
            tool_id=tool.id,
            action="service_integration",
            category="testing",
            status="success",
            message="Service integration test running.",
        )

        if audit is None:
            raise RuntimeError(
                "Audit event was not created."
            )

        print("AUDIT SERVICE: PASS")

        # 10. COMPLETE TASK
        task_service.complete_task(
            task.id,
            {
                "status": "service_integration_passed",
            },
        )

        print("TASK COMPLETION: PASS")

        print()
        print("=" * 60)
        print("ALL SERVICE INTEGRATION TESTS PASSED")
        print("=" * 60)


if __name__ == "__main__":
    main()