import threading
from uuid import uuid4

import pytest

from core.result import Result
from database.repositories.task_repository import TaskRepository
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
            password_hash="test-hash-not-used",
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


def test_execution_orchestrator_updates_task_status_to_completed() -> None:
    with session_scope() as session:
        user_service = UserService(session)
        user = user_service.create_user(
            email=f"orchestrator-success-{uuid4()}@example.com",
            name="Execution Orchestrator Success User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)
        task = task_service.create_task(
            user_id=user.id,
            title="Orchestrator Success Task",
            description="Testing successful execution orchestration.",
        )

        assert task.status == "pending"

        agent_service = AgentService(session)
        agent = agent_service.register_agent(
            name=f"Orchestrator Success Agent {uuid4()}",
            agent_type="coding",
            description="Testing success execution orchestration.",
            model_provider="local",
            model_name="test-model",
            capabilities=["execution", "testing"],
        )

        orchestrator = ExecutionOrchestrator(session)

        def operation(context):
            reloaded = task_service.get_task(task.id)
            assert reloaded is not None
            assert reloaded.status == "running"
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
            permissions={"read", "write", "execute"},
        )

        assert result.is_success()

        reloaded = task_service.get_task(task.id)
        assert reloaded is not None
        assert reloaded.status == "completed"
        assert reloaded.result_json["message"] == (
            "Orchestrated execution completed."
        )


def test_execution_orchestrator_updates_task_status_to_failed() -> None:
    with session_scope() as session:
        user_service = UserService(session)
        user = user_service.create_user(
            email=f"orchestrator-failure-{uuid4()}@example.com",
            name="Execution Orchestrator Failure User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)
        task = task_service.create_task(
            user_id=user.id,
            title="Orchestrator Failure Task",
            description="Testing failed execution orchestration.",
        )

        assert task.status == "pending"

        agent_service = AgentService(session)
        agent = agent_service.register_agent(
            name=f"Orchestrator Failure Agent {uuid4()}",
            agent_type="coding",
            description="Testing failure execution orchestration.",
            model_provider="local",
            model_name="test-model",
            capabilities=["execution", "testing"],
        )

        orchestrator = ExecutionOrchestrator(session)

        def operation(context):
            reloaded = task_service.get_task(task.id)
            assert reloaded is not None
            assert reloaded.status == "running"
            return Result.fail(
                "EXPLICIT_FAILURE",
                "expected failure",
            )

        result = orchestrator.execute(
            task_id=task.id,
            user_id=user.id,
            agent_id=agent.id,
            operation=operation,
            workspace_root="D:\\AI_COMMAND_CENTER",
            working_directory="D:\\AI_COMMAND_CENTER",
            permissions={"read", "write", "execute"},
        )

        assert result.is_failure()
        assert result.error.code == "EXPLICIT_FAILURE"

        reloaded = task_service.get_task(task.id)
        assert reloaded is not None
        assert reloaded.status == "failed"
        assert reloaded.execution_id is not None
        assert reloaded.error_json == {
            "code": "EXPLICIT_FAILURE",
            "message": "expected failure",
        }


def test_execution_orchestrator_persists_execution_id_on_success() -> None:
    with session_scope() as session:
        user_service = UserService(session)
        user = user_service.create_user(
            email=f"orchestrator-persist-success-{uuid4()}@example.com",
            name="Execution Orchestrator Persist Success User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)
        task = task_service.create_task(
            user_id=user.id,
            title="Orchestrator Persist Success Task",
            description="Testing persisted execution id on success.",
        )

        agent_service = AgentService(session)
        agent = agent_service.register_agent(
            name=f"Orchestrator Persist Success Agent {uuid4()}",
            agent_type="coding",
            description="Testing persisted execution id on success.",
            model_provider="local",
            model_name="test-model",
            capabilities=["execution", "testing"],
        )

        orchestrator = ExecutionOrchestrator(session)

        def operation(context):
            return Result.ok(
                {
                    "message": "persisted execution id ok",
                    "execution_id": str(context.execution_id),
                }
            )

        result = orchestrator.execute(
            task_id=task.id,
            user_id=user.id,
            agent_id=agent.id,
            operation=operation,
            workspace_root="D:\\AI_COMMAND_CENTER",
            working_directory="D:\\AI_COMMAND_CENTER",
            permissions={"read", "write", "execute"},
        )

        assert result.is_success()

        reloaded = task_service.get_task(task.id)
        assert reloaded is not None
        assert reloaded.status == "completed"
        assert reloaded.execution_id is not None
        assert reloaded.result_json == {
            "message": "persisted execution id ok",
            "execution_id": reloaded.execution_id,
        }
        assert result.require_data()["execution_id"] == reloaded.execution_id


def test_task_start_persists_lease_metadata() -> None:
    with session_scope() as session:
        user_service = UserService(session)
        user = user_service.create_user(
            email=f"lease-start-{uuid4()}@example.com",
            name="Lease Start User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)
        task = task_service.create_task(
            user_id=user.id,
            title="Lease Start Task",
            description="Testing task lease creation.",
        )

        repository = TaskRepository(session)
        execution_id = f"lease-start-{uuid4()}"
        repository.mark_started(task, execution_id, lease_ttl_seconds=60)

        reloaded = repository.get_by_id(task.id)
        assert reloaded is not None
        assert reloaded.status == "running"
        assert reloaded.execution_id == execution_id
        assert reloaded.last_heartbeat_at is not None
        assert reloaded.lease_expires_at is not None
        assert reloaded.lease_expires_at > reloaded.last_heartbeat_at


def test_heartbeat_enforces_execution_ownership() -> None:
    with session_scope() as session:
        user_service = UserService(session)
        user = user_service.create_user(
            email=f"lease-heartbeat-{uuid4()}@example.com",
            name="Lease Heartbeat User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)
        task = task_service.create_task(
            user_id=user.id,
            title="Lease Heartbeat Task",
            description="Testing heartbeat ownership enforcement.",
        )

        repository = TaskRepository(session)
        execution_id = f"lease-owner-{uuid4()}"
        repository.mark_started(task, execution_id, lease_ttl_seconds=60)

        original_heartbeat = task.last_heartbeat_at
        original_expiration = task.lease_expires_at
        assert original_heartbeat is not None
        assert original_expiration is not None

        with pytest.raises(ValueError):
            repository.heartbeat(
                task,
                "different-owner",
                lease_ttl_seconds=120,
            )

        reloaded = repository.get_by_id(task.id)
        assert reloaded is not None
        assert reloaded.execution_id == execution_id
        assert reloaded.last_heartbeat_at == original_heartbeat
        assert reloaded.lease_expires_at == original_expiration

        repository.heartbeat(task, execution_id, lease_ttl_seconds=120)

        reloaded = repository.get_by_id(task.id)
        assert reloaded is not None
        assert reloaded.last_heartbeat_at is not None
        assert reloaded.lease_expires_at is not None
        assert reloaded.lease_expires_at > original_expiration


def test_lease_is_cleared_on_terminal_task_state() -> None:
    with session_scope() as session:
        user_service = UserService(session)
        user = user_service.create_user(
            email=f"lease-terminal-{uuid4()}@example.com",
            name="Lease Terminal User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)
        task = task_service.create_task(
            user_id=user.id,
            title="Lease Terminal Success Task",
            description="Testing lease cleanup on success.",
        )

        repository = TaskRepository(session)
        execution_id = f"lease-success-{uuid4()}"
        repository.mark_started(task, execution_id, lease_ttl_seconds=60)

        repository.mark_completed(
            task,
            {"message": "lease cleared on success"},
            execution_id=execution_id,
        )

        reloaded = repository.get_by_id(task.id)
        assert reloaded is not None
        assert reloaded.status == "completed"
        assert reloaded.lease_expires_at is None
        assert reloaded.last_heartbeat_at is None

        failed_task = task_service.create_task(
            user_id=user.id,
            title="Lease Terminal Failure Task",
            description="Testing lease cleanup on failure.",
        )
        failed_execution_id = f"lease-failure-{uuid4()}"
        repository.mark_started(failed_task, failed_execution_id, lease_ttl_seconds=60)

        repository.mark_failed(
            failed_task,
            {"code": "LEASE_FAILURE_TEST", "message": "lease cleared on failure"},
            execution_id=failed_execution_id,
        )

        failed_reloaded = repository.get_by_id(failed_task.id)
        assert failed_reloaded is not None
        assert failed_reloaded.status == "failed"
        assert failed_reloaded.lease_expires_at is None
        assert failed_reloaded.last_heartbeat_at is None


def test_task_start_is_atomic_across_concurrent_workers() -> None:
    with session_scope() as session:
        user_service = UserService(session)
        user = user_service.create_user(
            email=f"orchestrator-concurrency-{uuid4()}@example.com",
            name="Execution Orchestrator Concurrency User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)
        task = task_service.create_task(
            user_id=user.id,
            title="Orchestrator Concurrency Task",
            description="Testing atomic task start concurrency.",
        )

    barrier = threading.Barrier(2)
    successes: list[str] = []

    def worker(name: str) -> None:
        with session_scope() as worker_session:
            repository = TaskRepository(worker_session)
            task_row = repository.get_by_id(task.id)
            assert task_row is not None
            execution_id = f"concurrent-{name}-{uuid4()}"
            barrier.wait()
            try:
                repository.mark_started(task_row, execution_id)
                successes.append(execution_id)
            except ValueError:
                pass

    thread_one = threading.Thread(target=worker, args=("one",))
    thread_two = threading.Thread(target=worker, args=("two",))
    thread_one.start()
    thread_two.start()
    thread_one.join()
    thread_two.join()

    with session_scope() as session:
        refreshed = TaskService(session).get_task(task.id)
        assert refreshed is not None
        assert refreshed.status == "running"
        assert refreshed.execution_id is not None
        assert len(successes) == 1
        assert refreshed.execution_id in successes


if __name__ == "__main__":
    main()