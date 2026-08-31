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