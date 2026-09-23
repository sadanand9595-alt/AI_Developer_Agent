from uuid import uuid4

from database.session import session_scope
from services.task_service import TaskService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"task-service-{uuid4()}@example.com",
            name="Task Service Test User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user.id,
            title="Test AI Task",
            description="Testing TaskService lifecycle.",
            priority=10,
        )

        print("CREATED:", task.id)
        print("STATUS:", task.status)

        found = task_service.get_task(task.id)

        if found is None:
            raise RuntimeError(
                "Task could not be retrieved."
            )

        print("READ:", found.title)

        started = task_service.start_task(task.id)

        print("STARTED:", started.status)

        completed = task_service.complete_task(
            task.id,
            {
                "message": "Task completed successfully.",
            },
        )

        print("COMPLETED:", completed.status)
        print("RESULT:", completed.result_json)

        retry_task = task_service.create_task(
            user_id=user.id,
            title="Retry Test Task",
            description="Testing task retry lifecycle.",
        )

        task_service.start_task(retry_task.id)

        failed = task_service.fail_task(
            retry_task.id,
            {
                "error": "Simulated execution failure.",
            },
        )

        print("FAILED:", failed.status)

        retried = task_service.retry_task(
            retry_task.id
        )

        print("RETRY COUNT:", retried.retry_count)

        user_tasks = task_service.list_user_tasks(
            user.id
        )

        print(
            "USER TASKS:",
            len(user_tasks),
        )


if __name__ == "__main__":
    main()
def test_task_service_approval_pause_and_resume_preserves_execution_identity():
    from services.task_service import TaskService
    from database.repositories.user_repository import UserRepository
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-service-{uuid4().hex}@example.com",
            name="Phase 7.3 Service Test User",
            password_hash="phase73-password",
        )

        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user.id,
            title="Phase 7.3 Service Resume",
            description="Testing durable approval pause and resume through TaskService.",
        )

        execution_id = f"phase73-service-execution-{uuid4().hex}"

        started = task_service.start_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert started.status == TaskStatus.RUNNING.value
        assert started.execution_id == execution_id

        waiting = task_service.pause_for_approval(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert waiting.status == TaskStatus.WAITING_APPROVAL.value
        assert waiting.execution_id == execution_id
        assert waiting.lease_owner_id is None

        resumed = task_service.resume_waiting_approval(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert resumed.status == TaskStatus.RUNNING.value
        assert resumed.execution_id == execution_id
        assert resumed.lease_owner_id == execution_id
        assert resumed.retry_count == 0


def test_task_service_manual_pause_and_resume_preserves_execution_identity():
    from services.task_service import TaskService
    from database.repositories.user_repository import UserRepository
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase74-service-{uuid4().hex}@example.com",
            name="Phase 7.4 Service Test User",
            password_hash="phase74-password",
        )

        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user.id,
            title="Phase 7.4 Service Pause Resume",
            description=(
                "Testing manual pause and resume through TaskService."
            ),
        )

        execution_id = f"phase74-service-execution-{uuid4().hex}"

        started = task_service.start_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert started.status == TaskStatus.RUNNING.value
        assert started.execution_id == execution_id

        paused = task_service.pause(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert paused.status == TaskStatus.PAUSED.value
        assert paused.execution_id == execution_id
        assert paused.lease_owner_id is None
        assert paused.lease_expires_at is None
        assert paused.last_heartbeat_at is None

        resumed = task_service.resume_paused(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert resumed.status == TaskStatus.RUNNING.value
        assert resumed.execution_id == execution_id
        assert resumed.lease_owner_id == execution_id
        assert resumed.lease_expires_at is not None
        assert resumed.last_heartbeat_at is not None
        assert resumed.retry_count == 0


def test_task_service_manual_pause_rejects_wrong_execution_owner():
    from services.task_service import TaskService
    from database.repositories.user_repository import UserRepository
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase74-service-owner-{uuid4().hex}@example.com",
            name="Phase 7.4 Service Owner Test User",
            password_hash="phase74-password",
        )

        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user.id,
            title="Phase 7.4 Service Wrong Owner",
            description="Testing manual pause ownership.",
        )

        execution_id = f"phase74-service-execution-{uuid4().hex}"
        wrong_execution_id = f"phase74-service-wrong-{uuid4().hex}"

        task_service.start_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        try:
            task_service.pause(
                task.id,
                execution_id=wrong_execution_id,
                lease_owner_id=wrong_execution_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "TaskService manual pause must reject a wrong owner."
            )

        task = task_service.get_task(task.id)

        assert task is not None
        assert task.status == TaskStatus.RUNNING.value
        assert task.execution_id == execution_id
        assert task.lease_owner_id == execution_id


def test_task_service_manual_resume_rejects_non_paused_task():
    from services.task_service import TaskService
    from database.repositories.user_repository import UserRepository
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase74-service-state-{uuid4().hex}@example.com",
            name="Phase 7.4 Service State Test User",
            password_hash="phase74-password",
        )

        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user.id,
            title="Phase 7.4 Service Invalid Resume",
            description="Testing manual resume state validation.",
        )

        execution_id = f"phase74-service-execution-{uuid4().hex}"

        task_service.start_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        try:
            task_service.resume_paused(
                task.id,
                execution_id=execution_id,
                lease_owner_id=execution_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "TaskService manual resume must reject a running task."
            )

        task = task_service.get_task(task.id)

        assert task is not None
        assert task.status == TaskStatus.RUNNING.value
        assert task.execution_id == execution_id
