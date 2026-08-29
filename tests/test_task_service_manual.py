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