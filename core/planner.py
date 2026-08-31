"""
Planner foundation for AI Command Center.

Converts a user request into a validated, ordered execution plan.
The planner does not execute tasks. It only creates the plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.result import Result


@dataclass(frozen=True, slots=True)
class PlanStep:
    """A single step in an execution plan."""

    step_id: str
    name: str
    description: str
    action: str
    order: int
    requires_approval: bool = False
    metadata: dict[str, object] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Structured plan produced by the planner."""

    plan_id: str
    request: str
    steps: tuple[PlanStep, ...]
    metadata: dict[str, object] = field(
        default_factory=dict
    )

    @property
    def step_count(self) -> int:
        """Return the number of plan steps."""

        return len(self.steps)


class Planner:
    """Create validated execution plans."""

    def create_plan(
        self,
        request: str,
    ) -> Result[ExecutionPlan]:
        """Create a basic execution plan from a request."""

        if not isinstance(request, str):
            return Result.fail(
                "INVALID_REQUEST",
                "Planner request must be a string.",
            )

        normalized_request = request.strip()

        if not normalized_request:
            return Result.fail(
                "EMPTY_REQUEST",
                "Planner request cannot be empty.",
            )

        step = PlanStep(
            step_id=str(uuid4()),
            name="analyze_request",
            description=(
                "Analyze the user request and determine "
                "the required execution work."
            ),
            action="analyze",
            order=1,
        )

        plan = ExecutionPlan(
            plan_id=str(uuid4()),
            request=normalized_request,
            steps=(step,),
            metadata={
                "planner": "default",
                "version": "1.0",
            },
        )

        return Result.ok(plan)

    def validate_plan(
        self,
        plan: ExecutionPlan,
    ) -> Result[ExecutionPlan]:
        """Validate an execution plan."""

        if (
            not isinstance(plan.plan_id, str)
            or not plan.plan_id.strip()
        ):
            return Result.fail(
                "INVALID_PLAN_ID",
                "Plan ID cannot be empty.",
            )

        if (
            not isinstance(plan.request, str)
            or not plan.request.strip()
        ):
            return Result.fail(
                "INVALID_PLAN_REQUEST",
                "Plan request cannot be empty.",
            )

        if not plan.steps:
            return Result.fail(
                "EMPTY_PLAN",
                "Execution plan must contain at least one step.",
            )

        expected_order = 1

        for step in plan.steps:
            if (
                not isinstance(step.step_id, str)
                or not step.step_id.strip()
            ):
                return Result.fail(
                    "INVALID_STEP_ID",
                    "Plan step ID cannot be empty.",
                )

            if (
                not isinstance(step.name, str)
                or not step.name.strip()
            ):
                return Result.fail(
                    "INVALID_STEP_NAME",
                    "Plan step name cannot be empty.",
                )

            if (
                not isinstance(step.action, str)
                or not step.action.strip()
            ):
                return Result.fail(
                    "INVALID_STEP_ACTION",
                    "Plan step action cannot be empty.",
                )

            if step.order != expected_order:
                return Result.fail(
                    "INVALID_STEP_ORDER",
                    "Plan steps must have sequential order.",
                    details={
                        "expected": expected_order,
                        "actual": step.order,
                    },
                )

            expected_order += 1

        return Result.ok(plan)