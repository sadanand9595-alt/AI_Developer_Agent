from uuid import uuid4

from core.result import Result
from database.session import session_scope
from services.agent_service import AgentService
from services.execution_orchestrator import ExecutionOrchestrator
from services.task_service import TaskService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        # USER
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"orchestrator-{uuid4()}@example.com",
            name="Execution Orchestrator Test User",
        )

        print("USER: PASS")

        # TASK
        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user.id,
            title="Orchestrator Test Task",
            description="Testing complete execution orchestration.",
        )

        print("TASK CREATED:", task.id)

        # AGENT
        agent_service = AgentService(session)

        agent = agent_service.register_agent(
            name=f"Orchestrator Test Agent {uuid4()}",
            agent_type="coding",
            description="Testing execution orchestration.",
            model_provider="local",
            model_name="test-model",
            capabilities=[
                "execution",
                "testing",
            ],
        )

        print("AGENT CREATED:", agent.id)

        # ORCHESTRATOR
        orchestrator = ExecutionOrchestrator(
            session
        )

        def operation(context):
            return Result.ok(
                {
                    "message": "Orchestrated execution completed.",
                    "task_id": str(context.task_id),
                    "agent_id": str(context.agent_id),
                }
            )

        result = orchestrator.execute(
            task_id=task.id,
            user_id=user.id,
            agent_id=agent.id,
            operation=operation,
            workspace_root="D:\\AI_COMMAND_CENTER",
            working_directory="D:\\AI_COMMAND_CENTER",
            permissions={
                "read",
                "write",
                "execute",
            },
        )

        if result.is_failure():
            raise RuntimeError(
                result.error.message
            )

        print(
            "ORCHESTRATION RESULT:",
            result.require_data(),
        )

        # VERIFY TASK
        verified_task = task_service.get_task(
            task.id
        )

        if verified_task is None:
            raise RuntimeError(
                "Task could not be retrieved after execution."
            )

        print(
            "FINAL TASK STATUS:",
            verified_task.status,
        )

        if verified_task.status != "completed":
            raise RuntimeError(
                "Task should be completed."
            )

        print("TASK COMPLETION: PASS")

        print()
        print("=" * 60)
        print("EXECUTION ORCHESTRATOR: PASS")
        print("=" * 60)


if __name__ == "__main__":
    main()