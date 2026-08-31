from database.repositories.task_repository import TaskRepository
from database.repositories.user_repository import UserRepository
from database.session import session_scope


def main() -> None:
    with session_scope() as session:
        user_repository = UserRepository(session)

        user = user_repository.create(
            email="task-test@example.com",
            name="Task Test User",
            password_hash="test-hash-not-used",
        )

        task_repository = TaskRepository(session)

        task = task_repository.create(
            user_id=user.id,
            title="Test AI Task",
            description="Testing TaskRepository database operations.",
            priority=5,
        )

        print("CREATED:", task.id, task.status)

        found = task_repository.get_by_id(task.id)

        if found is None:
            raise RuntimeError("Task could not be read.")

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


if __name__ == "__main__":
    main()