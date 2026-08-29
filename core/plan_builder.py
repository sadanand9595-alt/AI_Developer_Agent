"""
Execution plan builder for AI Command Center.

Provides a controlled builder for creating ordered execution
plans from validated plan steps.
"""

from __future__ import annotations

from core.planner import ExecutionPlan, PlanStep
from core.result import Result
from uuid import uuid4


class PlanBuilder:
    """Build ordered ExecutionPlan instances."""

    def __init__(
        self,
        request: str,
    ) -> None:
        normalized_request = request.strip()

        if not normalized_request:
            raise ValueError(
                "Plan request cannot be empty."
            )

        self._request = normalized_request
        self._steps: list[PlanStep] = []

    def add_step(
        self,
        *,
        name: str,
        description: str,
        action: str,
        requires_approval: bool = False,
        metadata: dict[str, object] | None = None,
    ) -> "PlanBuilder":
        """Add the next ordered execution step."""

        normalized_name = name.strip()
        normalized_description = description.strip()
        normalized_action = action.strip()

        if not normalized_name:
            raise ValueError(
                "Step name cannot be empty."
            )

        if not normalized_description:
            raise ValueError(
                "Step description cannot be empty."
            )

        if not normalized_action:
            raise ValueError(
                "Step action cannot be empty."
            )

        step = PlanStep(
            step_id=str(uuid4()),
            name=normalized_name,
            description=normalized_description,
            action=normalized_action,
            order=len(self._steps) + 1,
            requires_approval=requires_approval,
            metadata=dict(metadata or {}),
        )

        self._steps.append(step)

        return self

    def step_count(self) -> int:
        """Return the number of configured steps."""

        return len(self._steps)

    def build(self) -> Result[ExecutionPlan]:
        """Build and return an execution plan."""

        if not self._steps:
            return Result.fail(
                "EMPTY_PLAN",
                "Cannot build a plan without steps.",
            )

        plan = ExecutionPlan(
            plan_id=str(uuid4()),
            request=self._request,
            steps=tuple(self._steps),
            metadata={
                "builder": "default",
                "version": "1.0",
            },
        )

        return Result.ok(plan)

    def clear(self) -> None:
        """Remove all configured steps."""

        self._steps.clear()