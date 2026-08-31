"""
Execution monitor for AI Command Center.

Provides a centralized monitoring interface over execution
tracking and execution events.
"""

from __future__ import annotations

from core.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)
from core.execution_event_bus import ExecutionEventBus
from core.execution_observer import (
    ExecutionObservation,
    ExecutionObserver,
)
from core.execution_tracker import (
    ExecutionProgress,
    ExecutionTracker,
)


class ExecutionMonitor:
    """Centralized execution monitoring service."""

    def __init__(
        self,
        tracker: ExecutionTracker,
        event_bus: ExecutionEventBus,
        observer: ExecutionObserver | None = None,
    ) -> None:
        if not isinstance(
            tracker,
            ExecutionTracker,
        ):
            raise TypeError(
                "Expected an ExecutionTracker instance."
            )

        if not isinstance(
            event_bus,
            ExecutionEventBus,
        ):
            raise TypeError(
                "Expected an ExecutionEventBus instance."
            )

        if observer is not None and not isinstance(
            observer,
            ExecutionObserver,
        ):
            raise TypeError(
                "Expected an ExecutionObserver instance."
            )

        self._tracker = tracker
        self._event_bus = event_bus

        self._observer = (
            observer
            if observer is not None
            else ExecutionObserver(
                event_bus
            )
        )

    def start(
        self,
        execution_id: str,
        *,
        task_id: str | None = None,
        total_steps: int,
    ) -> ExecutionProgress:
        """Start tracking and publish an execution-started event."""

        progress = self._tracker.start(
            execution_id,
            total_steps=total_steps,
        )

        self._event_bus.publish(
            ExecutionEvent.create(
                event_type=ExecutionEventType.STARTED,
                execution_id=execution_id,
                task_id=task_id,
                data={
                    "total_steps": total_steps,
                },
            )
        )

        return progress

    def start_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Mark a step as started and publish an event."""

        progress = self._tracker.start_step(
            execution_id,
            step_name,
        )

        self._event_bus.publish(
            ExecutionEvent.create(
                event_type=ExecutionEventType.STEP_STARTED,
                execution_id=execution_id,
                task_id=task_id,
                step_name=step_name,
            )
        )

        return progress

    def complete_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Complete a step and publish an event."""

        progress = self._tracker.complete_step(
            execution_id,
            step_name,
        )

        self._event_bus.publish(
            ExecutionEvent.create(
                event_type=ExecutionEventType.STEP_COMPLETED,
                execution_id=execution_id,
                task_id=task_id,
                step_name=step_name,
                data={
                    "completed_steps": (
                        progress.completed_steps
                    ),
                    "total_steps": (
                        progress.total_steps
                    ),
                    "progress_percent": (
                        progress.progress_percent
                    ),
                },
            )
        )

        if progress.status == "completed":
            self._event_bus.publish(
                ExecutionEvent.create(
                    event_type=ExecutionEventType.COMPLETED,
                    execution_id=execution_id,
                    task_id=task_id,
                )
            )

        return progress

    def complete(
        self,
        execution_id: str,
    ) -> ExecutionProgress:
        """
        Finalize tracked progress for an execution that completes
        without a driving step (e.g. a zero-step plan).

        Unlike other monitor operations, this does not publish an
        event: callers use this to reconcile tracker state after
        the execution's COMPLETED event has already been published.
        """

        return self._tracker.complete(
            execution_id
        )

    def fail(
        self,
        execution_id: str,
        *,
        task_id: str | None = None,
        step_name: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ExecutionProgress:
        """Mark an execution failed and publish an event."""

        progress = self._tracker.fail(
            execution_id,
            step_name=step_name,
        )

        self._event_bus.publish(
            ExecutionEvent.create(
                event_type=ExecutionEventType.FAILED,
                execution_id=execution_id,
                task_id=task_id,
                step_name=step_name,
                data={
                    "error_code": error_code,
                    "error_message": error_message,
                },
            )
        )

        return progress

    def cancel(
        self,
        execution_id: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Cancel an execution and publish an event."""

        progress = self._tracker.cancel(
            execution_id
        )

        self._event_bus.publish(
            ExecutionEvent.create(
                event_type=ExecutionEventType.CANCELLED,
                execution_id=execution_id,
                task_id=task_id,
            )
        )

        return progress

    def get_progress(
        self,
        execution_id: str,
    ) -> ExecutionProgress | None:
        """Return tracker progress."""

        return self._tracker.get(
            execution_id
        )

    def get_observation(
        self,
        execution_id: str,
    ) -> ExecutionObservation | None:
        """Return observer state."""

        return self._observer.get(
            execution_id
        )

    def active_progress(
        self,
    ) -> tuple[ExecutionProgress, ...]:
        """Return active tracked executions."""

        return self._tracker.active()

    def observation_count(self) -> int:
        """Return number of observed executions."""

        return self._observer.count()

    def close(self) -> None:
        """Release monitoring subscriptions."""

        self._observer.close()