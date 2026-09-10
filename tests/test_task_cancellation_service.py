from uuid import uuid4

from database.session import session_scope
from services.task_service import TaskService
from services.user_service import UserService


def test_task_service_cancel_task():
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"task-cancel-service-{uuid4()}@example.com",
            name="Task Cancellation Service User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)

        task = task_service.create_task(
            user_id=user.id,
            title="Task Cancellation Service Test",
            description="Testing TaskService cancellation.",
        )

        execution_id = f"service-cancel-{uuid4()}"

        started = task_service.start_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert started.status == "running"
        assert started.execution_id == execution_id
        assert started.lease_owner_id == execution_id

        cancelled = task_service.cancel_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert cancelled.status == "cancelled"
        assert cancelled.execution_id == execution_id
        assert cancelled.lease_owner_id is None
        assert cancelled.lease_expires_at is None
        assert cancelled.last_heartbeat_at is None
