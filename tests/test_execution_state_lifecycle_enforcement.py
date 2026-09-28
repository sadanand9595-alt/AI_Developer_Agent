from unittest.mock import Mock

import pytest

from core.exceptions import ValidationError
from core.types import TaskStatus
from services.execution_state_service import ExecutionStateService


@pytest.mark.parametrize(
    ("method_name", "source_status", "target_status"),
    [
        ("mark_started", TaskStatus.COMPLETED, TaskStatus.RUNNING),
        ("mark_success", TaskStatus.PENDING, TaskStatus.COMPLETED),
        ("mark_failure", TaskStatus.PENDING, TaskStatus.FAILED),
    ],
)
def test_invalid_lifecycle_transition_is_rejected_before_repository_call(
    method_name: str,
    source_status: TaskStatus,
    target_status: TaskStatus,
) -> None:
    repository = Mock()
    service = ExecutionStateService(repository)

    task = Mock()
    task.id = "test-task"
    task.status = source_status.value

    method = getattr(service, method_name)

    if method_name == "mark_started":
        result = method(task, execution_id="execution-1")
    elif method_name == "mark_success":
        result = method(task, execution_id="execution-1")
    else:
        result = method(task, execution_id="execution-1")

    assert result.is_failure()
    assert result.error is not None
    assert result.error.code in {
        "TASK_START_FAILED",
        "TASK_COMPLETION_FAILED",
        "TASK_FAILURE_UPDATE_FAILED",
    }

    repository_method = {
        "mark_started": repository.mark_started,
        "mark_success": repository.mark_completed,
        "mark_failure": repository.mark_failed,
    }[method_name]

    repository_method.assert_not_called()


def test_valid_lifecycle_transition_is_allowed() -> None:
    repository = Mock()
    service = ExecutionStateService(repository)

    task = Mock()
    task.id = "test-task"
    task.status = TaskStatus.PENDING.value

    result = service.mark_started(
        task,
        execution_id="execution-1",
    )

    assert result.is_success()
    repository.mark_started.assert_called_once_with(
        task,
        "execution-1",
        lease_owner_id=None,
    )
