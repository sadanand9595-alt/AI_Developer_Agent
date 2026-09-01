from uuid import uuid4

from core.types import TaskStatus
from database.repositories.task_repository import TaskRepository
from database.session import session_scope
from services.execution_state_service import ExecutionStateService
from services.task_service import TaskService
from services.user_service import UserService


def main() -> None:
    with session_scope() as session:
        user_service = UserService(session)

        user = user_service.create_user(
            email=f"execution-state-{uuid4()}@example.com",
            name="Execution State Test User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)

        repository = TaskRepository(session)

        state_service = ExecutionStateService(
            repository
        )

        # -------------------------------------------------
        # SUCCESS PATH
        # -------------------------------------------------

        success_task = task_service.create_task(
            user_id=user.id,
            title="Execution State Success Task",
            description="Testing successful execution state.",
        )

        print(
            "SUCCESS TASK CREATED:",
            success_task.id,
        )

        started = state_service.mark_started(
            success_task
        )

        if started.is_failure():
            raise RuntimeError(
                started.error.message
            )

        print("STARTED: PASS")

        completed = state_service.mark_success(
            success_task,
            {
                "message": "Execution completed successfully.",
            },
        )

        if completed.is_failure():
            raise RuntimeError(
                completed.error.message
            )

        print("COMPLETED: PASS")

        # -------------------------------------------------
        # FAILURE PATH
        # -------------------------------------------------

        failed_task = task_service.create_task(
            user_id=user.id,
            title="Execution State Failure Task",
            description="Testing failed execution state.",
        )

        started_failed = state_service.mark_started(
            failed_task
        )

        if started_failed.is_failure():
            raise RuntimeError(
                started_failed.error.message
            )

        failed = state_service.mark_failure(
            failed_task,
            {
                "error": "Simulated execution failure.",
            },
        )

        if failed.is_failure():
            raise RuntimeError(
                failed.error.message
            )

        print("FAILED: PASS")

        # -------------------------------------------------
        # RETRY PATH
        # -------------------------------------------------

        retried = state_service.increment_retry(
            failed_task
        )

        if retried.is_failure():
            raise RuntimeError(
                retried.error.message
            )

        print(
            "RETRY INCREMENT: PASS"
        )

        print(
            "RETRY COUNT:",
            failed_task.retry_count,
        )

        # -------------------------------------------------
        # FINAL CHECK
        # -------------------------------------------------

        if success_task.status != TaskStatus.COMPLETED.value:
            raise RuntimeError(
                "Successful task should be COMPLETED."
            )

        if failed_task.status != TaskStatus.FAILED.value:
            raise RuntimeError(
                "Failed task should be FAILED."
            )

        print(
            "SUCCESS STATUS:",
            success_task.status
        )

        print(
            "FAILURE STATUS:",
            failed_task.status
        )

        print()
        print("=" * 60)
        print("EXECUTION STATE SERVICE: PASS")
        print("=" * 60)


def test_execution_state_service_tracks_task_lifecycle() -> None:
    with session_scope() as session:
        user_service = UserService(session)
        user = user_service.create_user(
            email=f"execution-state-{uuid4()}@example.com",
            name="Execution State Test User",
            password_hash="test-hash-not-used",
        )

        task_service = TaskService(session)
        repository = TaskRepository(session)
        state_service = ExecutionStateService(repository)

        success_task = task_service.create_task(
            user_id=user.id,
            title="Execution State Success Task",
            description="Testing successful execution state.",
        )

        started = state_service.mark_started(success_task)
        assert started.is_success()
        assert success_task.status == "running"

        completed = state_service.mark_success(
            success_task,
            {"message": "Execution completed successfully."},
        )
        assert completed.is_success()
        assert success_task.status == "completed"

        failure_task = task_service.create_task(
            user_id=user.id,
            title="Execution State Failure Task",
            description="Testing failed execution state.",
        )

        started_failed = state_service.mark_started(failure_task)
        assert started_failed.is_success()
        assert failure_task.status == "running"

        failed = state_service.mark_failure(
            failure_task,
            {"error": "Simulated execution failure."},
        )
        assert failed.is_success()
        assert failure_task.status == "failed"

        retry = state_service.increment_retry(failure_task)
        assert retry.is_success()


if __name__ == "__main__":
    main()