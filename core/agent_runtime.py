"""
Agent runtime for AI Command Center.

Provides controlled lifecycle management for an agent execution.
The runtime is responsible for state transitions and execution
boundaries. It does not contain planning or tool execution logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from core.context import ExecutionContext
from core.lifecycle import AgentLifecycle
from core.result import Result
from core.types import AgentStatus


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class AgentExecution(Generic[T]):
    """Result of a controlled agent execution."""

    context: ExecutionContext
    status: AgentStatus
    result: Result[T]


class AgentRuntime:
    """
    Controlled runtime for executing an agent operation.

    Responsibilities:
    - Validate agent lifecycle transitions.
    - Associate execution with an ExecutionContext.
    - Execute a supplied operation.
    - Convert unexpected exceptions into Result failures.
    - Always return the agent to a stable lifecycle state.
    """

    def __init__(
        self,
        *,
        agent_id: str,
    ) -> None:
        if not agent_id.strip():
            raise ValueError(
                "Agent ID cannot be empty."
            )

        self._agent_id = agent_id
        self._status = AgentStatus.IDLE

    @property
    def agent_id(self) -> str:
        """Return the runtime agent ID."""

        return self._agent_id

    @property
    def status(self) -> AgentStatus:
        """Return the current agent status."""

        return self._status

    def start_planning(
        self,
    ) -> Result[AgentStatus]:
        """Transition the agent into planning."""

        return self._transition(
            AgentStatus.PLANNING
        )

    def start_running(
        self,
    ) -> Result[AgentStatus]:
        """Transition the agent into running."""

        return self._transition(
            AgentStatus.RUNNING
        )

    def wait(
        self,
    ) -> Result[AgentStatus]:
        """Transition the agent into waiting."""

        return self._transition(
            AgentStatus.WAITING
        )

    def mark_error(
        self,
    ) -> Result[AgentStatus]:
        """Transition the agent into an error state."""

        return self._transition(
            AgentStatus.ERROR
        )

    def stop(
        self,
    ) -> Result[AgentStatus]:
        """Return the agent to idle."""

        return self._transition(
            AgentStatus.IDLE
        )

    def disable(
        self,
    ) -> Result[AgentStatus]:
        """Disable the agent."""

        return self._transition(
            AgentStatus.DISABLED
        )

    def execute(
        self,
        *,
        context: ExecutionContext,
        operation: Callable[
            [ExecutionContext],
            Result[T],
        ],
    ) -> AgentExecution[T]:
        """
        Execute an operation inside the controlled runtime.

        The operation receives the immutable ExecutionContext.

        Planning/execution state transitions are managed by the
        runtime rather than by the supplied operation.
        """

        execution_context = context.with_agent(
            self._agent_id
        )

        planning_result = self.start_planning()

        if planning_result.is_failure():
            return AgentExecution(
                context=execution_context,
                status=self._status,
                result=Result.fail(
                    "AGENT_LIFECYCLE_ERROR",
                    (
                        "Agent could not enter planning state."
                    ),
                    details={
                        "agent_id": self._agent_id,
                        "status": self._status.value,
                    },
                ),
            )

        running_result = self.start_running()

        if running_result.is_failure():
            self._safe_idle()

            return AgentExecution(
                context=execution_context,
                status=self._status,
                result=Result.fail(
                    "AGENT_LIFECYCLE_ERROR",
                    (
                        "Agent could not enter running state."
                    ),
                    details={
                        "agent_id": self._agent_id,
                        "status": self._status.value,
                    },
                ),
            )

        try:
            result = operation(execution_context)

            if not isinstance(result, Result):
                self.mark_error()

                return AgentExecution(
                    context=execution_context,
                    status=self._status,
                    result=Result.fail(
                        "INVALID_OPERATION_RESULT",
                        (
                            "Agent operation must return "
                            "a Result instance."
                        ),
                    ),
                )

            if result.is_failure():
                self.mark_error()

                return AgentExecution(
                    context=execution_context,
                    status=self._status,
                    result=result,
                )

            self.stop()

            return AgentExecution(
                context=execution_context,
                status=self._status,
                result=result,
            )

        except Exception as exc:
            self.mark_error()

            return AgentExecution(
                context=execution_context,
                status=self._status,
                result=Result.fail(
                    "AGENT_EXECUTION_ERROR",
                    str(exc),
                    details={
                        "exception_type": type(
                            exc
                        ).__name__,
                    },
                ),
            )

    def _transition(
        self,
        target: AgentStatus,
    ) -> Result[AgentStatus]:
        """Perform a validated lifecycle transition."""

        try:
            self._status = AgentLifecycle.transition(
                self._status,
                target,
            )

            return Result.ok(self._status)

        except Exception as exc:
            return Result.fail(
                "INVALID_AGENT_TRANSITION",
                str(exc),
                details={
                    "agent_id": self._agent_id,
                    "current": self._status.value,
                    "target": target.value,
                },
            )

    def _safe_idle(self) -> None:
        """Attempt to return the runtime to idle."""

        if AgentLifecycle.can_transition(
            self._status,
            AgentStatus.IDLE,
        ):
            self._status = AgentStatus.IDLE