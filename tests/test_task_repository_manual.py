from uuid import uuid4

from database.repositories.task_repository import TaskRepository
from database.repositories.user_repository import UserRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        user_repository = UserRepository(session)

        unique_email = (
            f"task-test-{uuid4().hex}@example.com"
        )

        user = user_repository.create(
            email=unique_email,
            name="Task Test User",
            password_hash="test-hash-not-used",
        )

        task_repository = TaskRepository(session)

        task = task_repository.create(
            user_id=user.id,
            title="Test AI Task",
            description=(
                "Testing TaskRepository database operations."
            ),
            priority=5,
        )

        print("CREATED:", task.id, task.status)

        found = task_repository.get_by_id(task.id)

        if found is None:
            raise RuntimeError(
                "Task could not be read."
            )

        print("READ:", found.title)

        task_repository.mark_started(found)

        print("STARTED:", found.status)

        task_repository.increment_retry(found)

        print("RETRY COUNT:", found.retry_count)

        task_repository.mark_completed(
            found,
            {
                "message": "Task completed successfully.",
            },
        )

        print("COMPLETED:", found.status)
        print("RESULT:", found.result_json)

        # -------------------------------------------------
        # TERMINAL STATE PROTECTION
        # -------------------------------------------------
        #
        # A completed task must not be silently re-completed,
        # failed, or restarted -- each would corrupt the
        # already-persisted terminal state (overwriting
        # result_json/completed_at, or leaving a contradictory
        # status='failed' record with a stale result_json still
        # attached).
        # -------------------------------------------------

        stale_result = found.result_json

        try:
            task_repository.mark_completed(
                found,
                {"message": "Second completion."},
            )
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Completed task should not be re-completable."
            )

        try:
            task_repository.mark_failed(
                found,
                {"error": "Late failure."},
            )
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Completed task should not be failable."
            )

        try:
            task_repository.mark_started(found)
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Completed task should not be restartable."
            )

        if (
            found.status != "completed"
            or found.result_json != stale_result
        ):
            raise RuntimeError(
                "Terminal task state was mutated by a "
                "rejected transition."
            )

        print("TERMINAL STATE PROTECTION: PASS")

        # -------------------------------------------------
        # RETRY-AFTER-FAILURE STILL WORKS
        # -------------------------------------------------
        #
        # The terminal-state guard must not block the existing
        # retry pattern: increment_retry() followed by
        # mark_started() on a FAILED task must still succeed.
        # -------------------------------------------------

        retry_task = task_repository.create(
            user_id=user.id,
            title="Retry Task",
            description="Testing retry-after-failure.",
        )

        task_repository.mark_started(retry_task)

        task_repository.mark_failed(
            retry_task,
            {"error": "First attempt failed."},
        )

        try:
            task_repository.mark_failed(
                retry_task,
                {"error": "Second failure call."},
            )
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Failed task should not be re-failable."
            )

        task_repository.increment_retry(retry_task)
        task_repository.mark_started(retry_task)

        if retry_task.status != "running":
            raise RuntimeError(
                "Retry after failure should restart the task."
            )

        task_repository.mark_completed(
            retry_task,
            {"message": "Succeeded after retry."},
        )

        if retry_task.status != "completed":
            raise RuntimeError(
                "Task should complete after a successful retry."
            )

        print("RETRY AFTER FAILURE: PASS")


if __name__ == "__main__":
    main()


def test_task_repository_approval_pause_and_resume_preserves_execution_identity():
    from database.repositories.task_repository import TaskRepository
    from database.models.task import Task
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-{uuid4().hex}@example.com",
            name="Phase 7.3 Test User",
            password_hash="phase73-password",
        )

        task = Task(
            user_id=user.id,
            title="Phase 7.3 Resume Task",
            description="Testing durable approval pause and resume.",
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.flush()

        repository = TaskRepository(session)

        execution_id = f"phase73-execution-{uuid4().hex}"

        started = repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert started.status == TaskStatus.RUNNING.value
        assert started.execution_id == execution_id
        assert started.lease_owner_id == execution_id

        waiting = repository.mark_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert waiting.status == TaskStatus.WAITING_APPROVAL.value
        assert waiting.execution_id == execution_id

        resumed = repository.resume_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert resumed.status == TaskStatus.RUNNING.value
        assert resumed.execution_id == execution_id
        assert resumed.lease_owner_id == execution_id
        assert resumed.retry_count == 0

def test_task_repository_approval_pause_rejects_wrong_execution_owner():
    from database.repositories.task_repository import TaskRepository
    from database.models.task import Task
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-owner-{uuid4().hex}@example.com",
            name="Phase 7.3 Owner Test User",
            password_hash="phase73-password",
        )

        task = Task(
            user_id=user.id,
            title="Phase 7.3 Wrong Owner Pause",
            description="Testing approval pause ownership.",
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.flush()

        repository = TaskRepository(session)

        execution_id = f"phase73-execution-{uuid4().hex}"
        wrong_execution_id = f"phase73-wrong-{uuid4().hex}"

        repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        try:
            repository.mark_waiting_approval(
                task,
                execution_id=wrong_execution_id,
                lease_owner_id=wrong_execution_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Approval pause must reject a wrong execution owner."
            )

        session.refresh(task)

        assert task.status == TaskStatus.RUNNING.value
        assert task.execution_id == execution_id


def test_task_repository_approval_resume_rejects_wrong_execution_identity():
    from database.repositories.task_repository import TaskRepository
    from database.models.task import Task
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-resume-{uuid4().hex}@example.com",
            name="Phase 7.3 Resume Owner Test User",
            password_hash="phase73-password",
        )

        task = Task(
            user_id=user.id,
            title="Phase 7.3 Wrong Resume Identity",
            description="Testing approval resume ownership.",
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.flush()

        repository = TaskRepository(session)

        execution_id = f"phase73-execution-{uuid4().hex}"
        wrong_execution_id = f"phase73-wrong-{uuid4().hex}"

        repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        repository.mark_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        try:
            repository.resume_waiting_approval(
                task,
                execution_id=wrong_execution_id,
                lease_owner_id=wrong_execution_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Approval resume must reject a wrong execution identity."
            )

        session.refresh(task)

        assert task.status == TaskStatus.WAITING_APPROVAL.value
        assert task.execution_id == execution_id
        assert task.lease_owner_id is None


def test_task_repository_approval_resume_acquires_fresh_lease_without_retry():
    from database.repositories.task_repository import TaskRepository
    from database.models.task import Task
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-lease-{uuid4().hex}@example.com",
            name="Phase 7.3 Lease Test User",
            password_hash="phase73-password",
        )

        task = Task(
            user_id=user.id,
            title="Phase 7.3 Fresh Lease",
            description="Testing fresh lease acquisition.",
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.flush()

        repository = TaskRepository(session)

        execution_id = f"phase73-execution-{uuid4().hex}"

        repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
            lease_ttl_seconds=60,
        )

        original_retry_count = task.retry_count
        original_lease_expires_at = task.lease_expires_at

        repository.mark_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert task.status == TaskStatus.WAITING_APPROVAL.value
        assert task.lease_owner_id is None
        assert task.lease_expires_at is None
        assert task.last_heartbeat_at is None

        repository.resume_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
            lease_ttl_seconds=300,
        )

        assert task.status == TaskStatus.RUNNING.value
        assert task.execution_id == execution_id
        assert task.lease_owner_id == execution_id
        assert task.lease_expires_at is not None
        assert task.last_heartbeat_at is not None
        assert task.retry_count == original_retry_count
        assert task.lease_expires_at != original_lease_expires_at


def test_task_repository_approval_resume_rejects_non_waiting_task():
    from database.repositories.task_repository import TaskRepository
    from database.models.task import Task
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-state-{uuid4().hex}@example.com",
            name="Phase 7.3 State Test User",
            password_hash="phase73-password",
        )

        task = Task(
            user_id=user.id,
            title="Phase 7.3 Invalid Resume State",
            description="Testing invalid approval resume state.",
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.flush()

        repository = TaskRepository(session)

        execution_id = f"phase73-execution-{uuid4().hex}"

        repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        try:
            repository.resume_waiting_approval(
                task,
                execution_id=execution_id,
                lease_owner_id=execution_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Approval resume must reject a non-waiting task."
            )

        session.refresh(task)

        assert task.status == TaskStatus.RUNNING.value
        assert task.execution_id == execution_id
def test_task_repository_approval_pause_rejects_wrong_execution_owner():
    from database.repositories.task_repository import TaskRepository
    from database.models.task import Task
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-owner-{uuid4().hex}@example.com",
            name="Phase 7.3 Owner Test User",
            password_hash="phase73-password",
        )

        task = Task(
            user_id=user.id,
            title="Phase 7.3 Wrong Owner Pause",
            description="Testing approval pause ownership.",
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.flush()

        repository = TaskRepository(session)

        execution_id = f"phase73-execution-{uuid4().hex}"
        wrong_execution_id = f"phase73-wrong-{uuid4().hex}"

        repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        try:
            repository.mark_waiting_approval(
                task,
                execution_id=wrong_execution_id,
                lease_owner_id=wrong_execution_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Approval pause must reject a wrong execution owner."
            )

        session.refresh(task)

        assert task.status == TaskStatus.RUNNING.value
        assert task.execution_id == execution_id


def test_task_repository_approval_resume_rejects_wrong_execution_identity():
    from database.repositories.task_repository import TaskRepository
    from database.models.task import Task
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-resume-{uuid4().hex}@example.com",
            name="Phase 7.3 Resume Owner Test User",
            password_hash="phase73-password",
        )

        task = Task(
            user_id=user.id,
            title="Phase 7.3 Wrong Resume Identity",
            description="Testing approval resume ownership.",
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.flush()

        repository = TaskRepository(session)

        execution_id = f"phase73-execution-{uuid4().hex}"
        wrong_execution_id = f"phase73-wrong-{uuid4().hex}"

        repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        repository.mark_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        try:
            repository.resume_waiting_approval(
                task,
                execution_id=wrong_execution_id,
                lease_owner_id=wrong_execution_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Approval resume must reject a wrong execution identity."
            )

        session.refresh(task)

        assert task.status == TaskStatus.WAITING_APPROVAL.value
        assert task.execution_id == execution_id
        assert task.lease_owner_id is None


def test_task_repository_approval_resume_acquires_fresh_lease_without_retry():
    from database.repositories.task_repository import TaskRepository
    from database.models.task import Task
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-lease-{uuid4().hex}@example.com",
            name="Phase 7.3 Lease Test User",
            password_hash="phase73-password",
        )

        task = Task(
            user_id=user.id,
            title="Phase 7.3 Fresh Lease",
            description="Testing fresh lease acquisition.",
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.flush()

        repository = TaskRepository(session)

        execution_id = f"phase73-execution-{uuid4().hex}"

        repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
            lease_ttl_seconds=60,
        )

        original_retry_count = task.retry_count
        original_lease_expires_at = task.lease_expires_at

        repository.mark_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        assert task.status == TaskStatus.WAITING_APPROVAL.value
        assert task.lease_owner_id is None
        assert task.lease_expires_at is None
        assert task.last_heartbeat_at is None

        repository.resume_waiting_approval(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
            lease_ttl_seconds=300,
        )

        assert task.status == TaskStatus.RUNNING.value
        assert task.execution_id == execution_id
        assert task.lease_owner_id == execution_id
        assert task.lease_expires_at is not None
        assert task.last_heartbeat_at is not None
        assert task.retry_count == original_retry_count
        assert task.lease_expires_at != original_lease_expires_at


def test_task_repository_approval_resume_rejects_non_waiting_task():
    from database.repositories.task_repository import TaskRepository
    from database.models.task import Task
    from core.types import TaskStatus
    from uuid import uuid4

    with session_scope() as session:
        user = UserRepository(session).create(
            email=f"phase73-state-{uuid4().hex}@example.com",
            name="Phase 7.3 State Test User",
            password_hash="phase73-password",
        )

        task = Task(
            user_id=user.id,
            title="Phase 7.3 Invalid Resume State",
            description="Testing invalid approval resume state.",
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.flush()

        repository = TaskRepository(session)

        execution_id = f"phase73-execution-{uuid4().hex}"

        repository.mark_started(
            task,
            execution_id=execution_id,
            lease_owner_id=execution_id,
        )

        try:
            repository.resume_waiting_approval(
                task,
                execution_id=execution_id,
                lease_owner_id=execution_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Approval resume must reject a non-waiting task."
            )

        session.refresh(task)

        assert task.status == TaskStatus.RUNNING.value
        assert task.execution_id == execution_id
