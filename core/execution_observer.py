"""
Execution observer for AI Command Center.

Consumes execution events and maintains an observable snapshot
of execution state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock

from core.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)
from core.execution_event_bus import ExecutionEventBus


@dataclass(slots=True)
class ExecutionObservation:
    """Current observed state of an execution."""

    execution_id: str
    task_id: str | None = None

    status: str = "pending"

    current_step: str | None = None

    completed_steps: int = 0
    total_steps: int = 0

    last_event_type: str | None = None

    last_event_at: datetime | None = None

    events_received: int = 0

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    @property
    def progress_percent(self) -> float:
        """Return observed execution progress."""

        if self.total_steps <= 0:
            return 0.0

        completed = min(
            self.completed_steps,
            self.total_steps,
        )

        return round(
            (completed / self.total_steps) * 100,
            2,
        )


class ExecutionObserver:
    """Observes execution events and maintains snapshots."""

    def __init__(
        self,
        event_bus: ExecutionEventBus,
    ) -> None:
        self._event_bus = event_bus

        self._observations: dict[
            str,
            ExecutionObservation,
        ] = {}

        self._lock = RLock()

        self._event_bus.subscribe(
            self._handle_event
        )

    def observe(
        self,
        event: ExecutionEvent,
    ) -> None:
        """Process an execution event manually."""

        self._handle_event(event)

    def get(
        self,
        execution_id: str,
    ) -> ExecutionObservation | None:
        """Return the current observation."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return None

        with self._lock:
            return self._observations.get(
                normalized_id
            )

    def count(self) -> int:
        """Return the number of observed executions."""

        with self._lock:
            return len(
                self._observations
            )

    def all(
        self,
    ) -> tuple[ExecutionObservation, ...]:
        """Return all execution observations."""

        with self._lock:
            return tuple(
                self._observations.values()
            )

    def remove(
        self,
        execution_id: str,
    ) -> bool:
        """Remove an execution observation."""

        normalized_id = execution_id.strip()

        if not normalized_id:
            return False

        with self._lock:
            return (
                self._observations.pop(
                    normalized_id,
                    None,
                )
                is not None
            )

    def clear(self) -> None:
        """Remove all observations."""

        with self._lock:
            self._observations.clear()

    def close(self) -> None:
        """Detach the observer from the event bus."""

        self._event_bus.unsubscribe(
            self._handle_event
        )

    def _handle_event(
        self,
        event: ExecutionEvent,
    ) -> None:
        """Update an observation from an event."""

        execution_id = event.execution_id

        with self._lock:
            observation = self._observations.get(
                execution_id
            )

            if observation is None:
                observation = ExecutionObservation(
                    execution_id=execution_id,
                    task_id=event.task_id,
                )

                self._observations[
                    execution_id
                ] = observation

            if (
                observation.task_id is None
                and event.task_id is not None
            ):
                observation.task_id = event.task_id

            observation.last_event_type = (
                event.event_type
            )

            observation.last_event_at = (
                event.timestamp
            )

            observation.events_received += 1

            self._apply_event(
                observation,
                event,
            )

    @staticmethod
    def _apply_event(
        observation: ExecutionObservation,
        event: ExecutionEvent,
    ) -> None:
        """Apply event-specific state changes."""

        if event.event_type == (
            ExecutionEventType.STARTED
        ):
            observation.status = "running"

            if isinstance(
                event.data,
                dict,
            ):
                total_steps = event.data.get(
                    "total_steps"
                )

                if isinstance(
                    total_steps,
                    int,
                ) and total_steps >= 0:
                    observation.total_steps = (
                        total_steps
                    )

            return

        if event.event_type == (
            ExecutionEventType.STEP_STARTED
        ):
            observation.status = "running"
            observation.current_step = (
                event.step_name
            )
            return

        if event.event_type == (
            ExecutionEventType.STEP_COMPLETED
        ):
            if event.step_name:
                observation.current_step = (
                    event.step_name
                )

            if (
                observation.completed_steps
                < observation.total_steps
            ):
                observation.completed_steps += 1

            if isinstance(
                event.data,
                dict,
            ):
                total_steps = event.data.get(
                    "total_steps"
                )

                if isinstance(
                    total_steps,
                    int,
                ) and total_steps >= 0:
                    observation.total_steps = (
                        total_steps
                    )

            return

        if event.event_type == (
            ExecutionEventType.COMPLETED
        ):
            observation.status = "completed"

            if observation.total_steps > 0:
                observation.completed_steps = (
                    observation.total_steps
                )

            observation.current_step = None
            return

        if event.event_type == (
            ExecutionEventType.FAILED
        ):
            observation.status = "failed"
            return

        if event.event_type == (
            ExecutionEventType.CANCELLED
        ):
            observation.status = "cancelled"
            return