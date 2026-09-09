from uuid import uuid4

from database.repositories.task_repository import TaskRepository
from database.session import session_scope
from database.repositories.user_repository import UserRepository
from services.task_service import TaskService


def main() -> None:
    with session_scope() as session:
        user_repository = UserRepository(session)

        user_one = user_repository.create(
            email=f"agent-history-one-{uuid4().hex}@example.com",
            name="Agent History User One",
            password_hash="test-hash-not-used",
        )

        user_two = user_repository.create(
            email=f"agent-history-two-{uuid4().hex}@example.com",
            name="Agent History User Two",
            password_hash="test-hash-not-used",
        )

        agent_id = str(uuid4())
        other_agent_id = str(uuid4())

        task_repository = TaskRepository(session)

        # -------------------------------------------------
        # AGENT-LINKED TASK CREATION
        # -------------------------------------------------

        agent_task = task_repository.create(
            user_id=user_one.id,
            title="Agent Execution Task",
            description="Testing agent-linked task persistence.",
            agent_id=agent_id,
        )

        if agent_task.agent_id != agent_id:
            raise RuntimeError(
                "Agent ID was not persisted on the task."
            )

        if agent_task.status != "pending":
            raise RuntimeError(
                "Agent-linked task should start as pending."
            )

        print("AGENT ID PERSISTENCE: PASS")

        # -------------------------------------------------
        # EXECUTION ID LOOKUP
        # -------------------------------------------------

        execution_id = str(uuid4())

        task_repository.mark_started(
            agent_task,
            execution_id=execution_id,
        )

        found = task_repository.get_by_execution_id(
            execution_id
        )

        if found is None:
            raise RuntimeError(
                "Task could not be found by execution ID."
            )

        if found.id != agent_task.id:
            raise RuntimeError(
                "Execution ID lookup returned the wrong task."
            )

        print("EXECUTION ID LOOKUP: PASS")

        # -------------------------------------------------
        # USER-SCOPED EXECUTION LOOKUP
        # -------------------------------------------------

        found_for_owner = (
            task_repository.get_by_execution_id_and_user(
                execution_id,
                user_one.id,
            )
        )

        if found_for_owner is None:
            raise RuntimeError(
                "Task owner could not retrieve their execution."
            )

        found_for_other_user = (
            task_repository.get_by_execution_id_and_user(
                execution_id,
                user_two.id,
            )
        )

        if found_for_other_user is not None:
            raise RuntimeError(
                "Execution leaked across users."
            )

        print("USER ISOLATION: PASS")

        # -------------------------------------------------
        # AGENT LISTING
        # -------------------------------------------------

        another_agent_task = task_repository.create(
            user_id=user_one.id,
            title="Second Agent Execution",
            description="Testing agent execution listing.",
            agent_id=agent_id,
        )

        unrelated_task = task_repository.create(
            user_id=user_one.id,
            title="Unrelated Task",
            description="Should not appear in agent history.",
            agent_id=other_agent_id,
        )

        agent_tasks = task_repository.list_by_agent(
            agent_id
        )

        agent_task_ids = {
            task.id
            for task in agent_tasks
        }

        if agent_task.id not in agent_task_ids:
            raise RuntimeError(
                "Agent execution missing from agent listing."
            )

        if another_agent_task.id not in agent_task_ids:
            raise RuntimeError(
                "Second agent execution missing from listing."
            )

        if unrelated_task.id in agent_task_ids:
            raise RuntimeError(
                "Unrelated agent task appeared in listing."
            )

        print("AGENT LISTING: PASS")

        # -------------------------------------------------
        # USER-SCOPED AGENT LISTING
        # -------------------------------------------------

        user_two_agent_task = task_repository.create(
            user_id=user_two.id,
            title="Other User Agent Execution",
            description="Testing user-scoped agent history.",
            agent_id=agent_id,
        )

        user_one_agent_tasks = (
            task_repository.list_by_agent_and_user(
                agent_id,
                user_one.id,
            )
        )

        user_one_ids = {
            task.id
            for task in user_one_agent_tasks
        }

        if agent_task.id not in user_one_ids:
            raise RuntimeError(
                "Owner's agent execution is missing."
            )

        if another_agent_task.id not in user_one_ids:
            raise RuntimeError(
                "Owner's second agent execution is missing."
            )

        if user_two_agent_task.id in user_one_ids:
            raise RuntimeError(
                "Other user's agent execution leaked."
            )

        user_two_agent_tasks = (
            task_repository.list_by_agent_and_user(
                agent_id,
                user_two.id,
            )
        )

        user_two_ids = {
            task.id
            for task in user_two_agent_tasks
        }

        if user_two_agent_task.id not in user_two_ids:
            raise RuntimeError(
                "Other user's own execution is missing."
            )

        print("SCOPED AGENT LISTING: PASS")

        # -------------------------------------------------
        # TASK SERVICE
        # -------------------------------------------------

        task_service = TaskService(session)

        service_task = task_service.create_task(
            user_id=user_one.id,
            title="Service Agent Execution",
            description="Testing TaskService agent support.",
            agent_id=agent_id,
        )

        if service_task.agent_id != agent_id:
            raise RuntimeError(
                "TaskService did not persist agent_id."
            )

        service_execution_id = str(uuid4())

        task_service.start_task(
            service_task.id,
            execution_id=service_execution_id,
        )

        service_found = task_service.get_task_by_execution_id(
            service_execution_id
        )

        if service_found is None:
            raise RuntimeError(
                "TaskService execution lookup failed."
            )

        if service_found.id != service_task.id:
            raise RuntimeError(
                "TaskService returned the wrong execution."
            )

        owner_execution = task_service.get_agent_execution(
            agent_id=agent_id,
            execution_id=service_execution_id,
            user_id=user_one.id,
        )

        if owner_execution is None:
            raise RuntimeError(
                "TaskService owner execution lookup failed."
            )

        wrong_agent_execution = (
            task_service.get_agent_execution(
                agent_id=other_agent_id,
                execution_id=service_execution_id,
                user_id=user_one.id,
            )
        )

        if wrong_agent_execution is not None:
            raise RuntimeError(
                "TaskService returned execution for wrong agent."
            )

        other_user_execution = (
            task_service.get_agent_execution(
                agent_id=agent_id,
                execution_id=service_execution_id,
                user_id=user_two.id,
            )
        )

        if other_user_execution is not None:
            raise RuntimeError(
                "TaskService leaked execution across users."
            )

        service_history = (
            task_service.list_agent_executions(
                agent_id=agent_id,
                user_id=user_one.id,
            )
        )

        service_history_ids = {
            task.id
            for task in service_history
        }

        if service_task.id not in service_history_ids:
            raise RuntimeError(
                "TaskService agent history is missing execution."
            )

        print("TASK SERVICE AGENT HISTORY: PASS")

        print("PHASE 5 TASK AGENT HISTORY: PASS")


if __name__ == "__main__":
    main()
