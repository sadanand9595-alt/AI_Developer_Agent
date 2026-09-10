from __future__ import annotations

from uuid import uuid4

import pytest

from core.types import TaskStatus
from database.models.task import Task
from database.repositories.task_repository import TaskRepository
from database.session import session_scope
from services.task_service import TaskService
from services.user_service import UserService


def _unique_id() -> str:
    return str(uuid4())


def _create_user(db):
    return UserService(db).create_user(
        email=f"retry-test-{_unique_id()}@example.com",
        name="Retry Test User",
        password_hash="test-password-hash",
    )


def _create_task(
    db,
    *,
    user_id: str | None = None,
    agent_id: str | None = None,
) -> Task:
    if user_id is None:
        user = _create_user(db)
        user_id = user.id

    return TaskService(db).create_task(
        user_id=user_id,
        title="Retry test task",
        description="Execute retry test",
        agent_id=agent_id,
    )


def _fail_task(
    db,
    task: Task,
    *,
    execution_id: str | None = None,
) -> Task:
    service = TaskService(db)

    execution_id = execution_id or _unique_id()

    service.start_task(
        task.id,
        execution_id=execution_id,
        lease_owner_id=execution_id,
    )

    return service.fail_task(
        task.id,
        error={
            "code": "TEST_FAILURE",
            "message": "Intentional test failure.",
        },
        execution_id=execution_id,
        lease_owner_id=execution_id,
    )


def test_retry_failed_task_transitions_to_running():
    with session_scope() as db:
        task = _fail_task(db, _create_task(db))

        assert task.status == TaskStatus.FAILED.value
        assert task.retry_count == 0

        execution_id = _unique_id()

        retried = TaskService(db).retry_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert retried.status == TaskStatus.RUNNING.value
        assert retried.retry_count == 1
        assert retried.execution_id == execution_id
        assert retried.lease_owner_id == execution_id
        assert retried.error_json is None
        assert retried.result_json is None
        assert retried.started_at is not None
        assert retried.last_heartbeat_at is not None
        assert retried.lease_expires_at is not None


def test_retry_failed_task_uses_new_execution_id():
    with session_scope() as db:
        task = _create_task(db)
        original_execution_id = _unique_id()

        task = _fail_task(
            db,
            task,
            execution_id=original_execution_id,
        )

        new_execution_id = _unique_id()

        retried = TaskService(db).retry_task(
            task.id,
            execution_id=new_execution_id,
            lease_owner_id=new_execution_id,
        )

        assert retried.execution_id != original_execution_id
        assert retried.execution_id == new_execution_id


def test_retry_failed_task_increments_retry_count_each_time():
    with session_scope() as db:
        task = _create_task(db)

        first_execution_id = _unique_id()

        task = _fail_task(
            db,
            task,
            execution_id=first_execution_id,
        )

        assert task.retry_count == 0

        second_execution_id = _unique_id()

        task = TaskService(db).retry_task(
            task.id,
            execution_id=second_execution_id,
            lease_owner_id=second_execution_id,
        )

        assert task.retry_count == 1

        task = TaskService(db).fail_task(
            task.id,
            error={
                "code": "TEST_FAILURE_2",
                "message": "Second intentional failure.",
            },
            execution_id=second_execution_id,
            lease_owner_id=second_execution_id,
        )

        third_execution_id = _unique_id()

        task = TaskService(db).retry_task(
            task.id,
            execution_id=third_execution_id,
            lease_owner_id=third_execution_id,
        )

        assert task.retry_count == 2
        assert task.status == TaskStatus.RUNNING.value
        assert task.execution_id == third_execution_id


def test_retry_rejects_non_failed_task():
    with session_scope() as db:
        task = _create_task(db)
        execution_id = _unique_id()

        with pytest.raises(
            ValueError,
            match="Only failed tasks can be retried",
        ):
            TaskService(db).retry_task(
                task.id,
                execution_id=execution_id,
                lease_owner_id=execution_id,
            )


def test_retry_rejects_empty_execution_id():
    with session_scope() as db:
        task = _fail_task(db, _create_task(db))

        with pytest.raises(
            ValueError,
            match="execution_id cannot be empty",
        ):
            TaskService(db).retry_task(
                task.id,
                execution_id="   ",
            )


def test_retry_rejects_mismatched_lease_owner():
    with session_scope() as db:
        task = _fail_task(db, _create_task(db))

        execution_id = _unique_id()
        different_lease_owner = _unique_id()

        with pytest.raises(
            ValueError,
            match="lease_owner_id must match execution_id",
        ):
            TaskService(db).retry_task(
                task.id,
                execution_id=execution_id,
                lease_owner_id=different_lease_owner,
            )


def test_repository_retry_is_atomic_and_only_failed_task_is_retryable():
    with session_scope() as db:
        task = _fail_task(db, _create_task(db))

        repository = TaskRepository(db)

        first_execution_id = _unique_id()

        retried = repository.retry_failed_task(
            task,
            first_execution_id,
            lease_owner_id=first_execution_id,
        )

        assert retried.status == TaskStatus.RUNNING.value
        assert retried.retry_count == 1

        second_execution_id = _unique_id()

        with pytest.raises(
            ValueError,
            match="Task is not eligible for retry",
        ):
            repository.retry_failed_task(
                task,
                second_execution_id,
                lease_owner_id=second_execution_id,
            )


def test_retry_clears_previous_error():
    with session_scope() as db:
        task = _fail_task(db, _create_task(db))

        assert task.error_json is not None

        execution_id = _unique_id()

        retried = TaskService(db).retry_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert retried.error_json is None


def test_retry_rejects_completed_task_with_result():
    with session_scope() as db:
        task = _create_task(db)

        execution_id = _unique_id()

        service = TaskService(db)

        service.start_task(
            task.id,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        task = service.complete_task(
            task.id,
            {
                "output": {
                    "test": "result",
                },
            },
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert task.status == TaskStatus.COMPLETED.value
        assert task.result_json is not None

        with pytest.raises(
            ValueError,
            match="Only failed tasks can be retried",
        ):
            service.retry_task(
                task.id,
                execution_id=_unique_id(),
            )

