"""
Lifecycle management for AI Command Center.

This module provides controlled state transitions for tasks
and agents. Invalid state transitions are rejected explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.exceptions import ValidationError
from core.types import AgentStatus, TaskStatus


@dataclass(frozen=True, slots=True)
class LifecycleTransition:
    """Represents a valid state transition."""

    source: str
    target: str


class TaskLifecycle:
    """Controls valid transitions for task execution."""

    _TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
        TaskStatus.PENDING: frozenset(
            {
                TaskStatus.PLANNING,
                TaskStatus.RUNNING,
                TaskStatus.CANCELLED,
            }
        ),
        TaskStatus.PLANNING: frozenset(
            {
                TaskStatus.RUNNING,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            }
        ),
        TaskStatus.RUNNING: frozenset(
            {
                TaskStatus.WAITING_APPROVAL,
                TaskStatus.PAUSED,
                TaskStatus.VALIDATING,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            }
        ),
        TaskStatus.PAUSED: frozenset(
            {
                TaskStatus.RUNNING,
                TaskStatus.CANCELLED,
            }
        ),
        TaskStatus.WAITING_APPROVAL: frozenset(
            {
                TaskStatus.RUNNING,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            }
        ),
        TaskStatus.VALIDATING: frozenset(
            {
                TaskStatus.COMPLETED,
                TaskStatus.RUNNING,
                TaskStatus.FAILED,
            }
        ),
        TaskStatus.COMPLETED: frozenset(),
        TaskStatus.FAILED: frozenset(
            {
                TaskStatus.PLANNING,
                TaskStatus.RUNNING,
                TaskStatus.CANCELLED,
            }
        ),
        TaskStatus.CANCELLED: frozenset(),
    }

    @classmethod
    def allowed_targets(
        cls,
        current: TaskStatus,
    ) -> frozenset[TaskStatus]:
        """Return the immutable set of valid target states."""

        if not isinstance(current, TaskStatus):
            return frozenset()

        return cls._TRANSITIONS.get(
            current,
            frozenset(),
        )

    @classmethod
    def create_transition(
        cls,
        current: TaskStatus,
        target: TaskStatus,
    ) -> LifecycleTransition:
        """Validate and create an immutable lifecycle transition."""

        cls.transition(current, target)

        return LifecycleTransition(
            source=current.value,
            target=target.value,
        )

    @classmethod
    def can_transition(
        cls,
        current: TaskStatus,
        target: TaskStatus,
    ) -> bool:
        """Return whether a task transition is allowed."""

        if not isinstance(
            current,
            TaskStatus,
        ) or not isinstance(
            target,
            TaskStatus,
        ):
            return False

        return target in cls._TRANSITIONS.get(current, frozenset())

    @classmethod
    def transition(
        cls,
        current: TaskStatus,
        target: TaskStatus,
    ) -> TaskStatus:
        """
        Validate and perform a task transition.

        Raises:
            ValidationError: If the transition is invalid.
        """

        if not cls.can_transition(current, target):
            current_repr = getattr(
                current, "value", current
            )
            target_repr = getattr(
                target, "value", target
            )

            raise ValidationError(
                (
                    f"Invalid task transition: "
                    f"{current_repr} -> {target_repr}"
                ),
                details={
                    "current": current_repr,
                    "target": target_repr,
                },
            )

        return target


class AgentLifecycle:
    """Controls valid transitions for agent execution."""

    _TRANSITIONS: dict[AgentStatus, frozenset[AgentStatus]] = {
        AgentStatus.IDLE: frozenset(
            {
                AgentStatus.PLANNING,
                AgentStatus.DISABLED,
            }
        ),
        AgentStatus.PLANNING: frozenset(
            {
                AgentStatus.RUNNING,
                AgentStatus.ERROR,
                AgentStatus.IDLE,
            }
        ),
        AgentStatus.RUNNING: frozenset(
            {
                AgentStatus.WAITING,
                AgentStatus.ERROR,
                AgentStatus.IDLE,
            }
        ),
        AgentStatus.WAITING: frozenset(
            {
                AgentStatus.RUNNING,
                AgentStatus.ERROR,
                AgentStatus.IDLE,
            }
        ),
        AgentStatus.ERROR: frozenset(
            {
                AgentStatus.PLANNING,
                AgentStatus.IDLE,
                AgentStatus.DISABLED,
            }
        ),
        AgentStatus.DISABLED: frozenset(
            {
                AgentStatus.IDLE,
            }
        ),
    }

    @classmethod
    def can_transition(
        cls,
        current: AgentStatus,
        target: AgentStatus,
    ) -> bool:
        """Return whether an agent transition is allowed."""

        if not isinstance(
            current,
            AgentStatus,
        ) or not isinstance(
            target,
            AgentStatus,
        ):
            return False

        return target in cls._TRANSITIONS.get(current, frozenset())

    @classmethod
    def transition(
        cls,
        current: AgentStatus,
        target: AgentStatus,
    ) -> AgentStatus:
        """
        Validate and perform an agent transition.

        Raises:
            ValidationError: If the transition is invalid.
        """

        if not cls.can_transition(current, target):
            current_repr = getattr(
                current, "value", current
            )
            target_repr = getattr(
                target, "value", target
            )

            raise ValidationError(
                (
                    f"Invalid agent transition: "
                    f"{current_repr} -> {target_repr}"
                ),
                details={
                    "current": current_repr,
                    "target": target_repr,
                },
            )

        return target
