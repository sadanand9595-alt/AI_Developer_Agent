from core.exceptions import ValidationError
from core.lifecycle import LifecycleTransition, TaskLifecycle
from core.types import TaskStatus


def test_task_lifecycle_exposes_formal_transition() -> None:
    transition = TaskLifecycle.create_transition(
        TaskStatus.RUNNING,
        TaskStatus.PAUSED,
    )

    assert isinstance(
        transition,
        LifecycleTransition,
    )

    assert transition.source == TaskStatus.RUNNING.value
    assert transition.target == TaskStatus.PAUSED.value


def test_task_lifecycle_transition_is_immutable() -> None:
    transition = TaskLifecycle.create_transition(
        TaskStatus.RUNNING,
        TaskStatus.PAUSED,
    )

    try:
        transition.source = "changed"
    except AttributeError:
        pass
    else:
        raise AssertionError(
            "LifecycleTransition must be immutable."
        )


def test_task_lifecycle_rejects_invalid_formal_transition() -> None:
    try:
        TaskLifecycle.create_transition(
            TaskStatus.COMPLETED,
            TaskStatus.RUNNING,
        )
    except ValidationError as exc:
        assert "Invalid task transition" in str(exc)
    else:
        raise AssertionError(
            "Invalid transition should raise ValidationError."
        )


def test_task_lifecycle_lists_allowed_targets() -> None:
    targets = TaskLifecycle.allowed_targets(
        TaskStatus.RUNNING,
    )

    assert targets == frozenset(
        {
            TaskStatus.PAUSED,
            TaskStatus.WAITING_APPROVAL,
            TaskStatus.VALIDATING,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
    )


def test_task_lifecycle_rejects_non_task_status_values() -> None:
    assert (
        TaskLifecycle.can_transition(
            "running",
            TaskStatus.PAUSED,
        )
        is False
    )

    try:
        TaskLifecycle.create_transition(
            "running",
            TaskStatus.PAUSED,
        )
    except ValidationError:
        pass
    else:
        raise AssertionError(
            "Non-TaskStatus source must be rejected."
        )
