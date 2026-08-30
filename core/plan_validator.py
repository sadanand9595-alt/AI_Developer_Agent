"""
Execution plan validator for AI Command Center.

Validates planner output before a plan is allowed to proceed
to the execution layer.
"""

from __future__ import annotations

from core.planner import ExecutionPlan
from core.result import Result


class PlanValidator:
    """Validate execution plans."""

    def validate(
        self,
        plan: ExecutionPlan,
    ) -> Result[ExecutionPlan]:
        """Validate a complete execution plan."""

        if not isinstance(
            plan,
            ExecutionPlan,
        ):
            return Result.fail(
                "INVALID_PLAN_TYPE",
                "Expected an ExecutionPlan instance.",
            )

        if (
            not isinstance(plan.plan_id, str)
            or not plan.plan_id.strip()
        ):
            return Result.fail(
                "INVALID_PLAN_ID",
                "Plan ID must be a non-empty string.",
            )

        if (
            not isinstance(plan.request, str)
            or not plan.request.strip()
        ):
            return Result.fail(
                "INVALID_PLAN_REQUEST",
                "Plan request must be a non-empty string.",
            )

        if not plan.steps:
            return Result.fail(
                "EMPTY_PLAN",
                "Execution plan must contain at least one step.",
            )

        seen_step_ids: set[str] = set()
        seen_orders: set[int] = set()

        for step in plan.steps:
            if (
                not isinstance(step.step_id, str)
                or not step.step_id.strip()
            ):
                return Result.fail(
                    "INVALID_STEP_ID",
                    "Plan step ID must be a non-empty string.",
                )

            if step.step_id in seen_step_ids:
                return Result.fail(
                    "DUPLICATE_STEP_ID",
                    "Plan contains duplicate step IDs.",
                    details={
                        "step_id": step.step_id,
                    },
                )

            seen_step_ids.add(step.step_id)

            if (
                not isinstance(step.name, str)
                or not step.name.strip()
            ):
                return Result.fail(
                    "INVALID_STEP_NAME",
                    "Plan step name must be a non-empty string.",
                )

            if (
                not isinstance(step.description, str)
                or not step.description.strip()
            ):
                return Result.fail(
                    "INVALID_STEP_DESCRIPTION",
                    "Plan step description must be a non-empty string.",
                    details={
                        "step_id": step.step_id,
                    },
                )

            if (
                not isinstance(step.action, str)
                or not step.action.strip()
            ):
                return Result.fail(
                    "INVALID_STEP_ACTION",
                    "Plan step action must be a non-empty string.",
                    details={
                        "step_id": step.step_id,
                    },
                )

            if (
                not isinstance(step.order, int)
                or isinstance(step.order, bool)
                or step.order <= 0
            ):
                return Result.fail(
                    "INVALID_STEP_ORDER",
                    "Plan step order must be greater than zero.",
                    details={
                        "step_id": step.step_id,
                        "order": step.order,
                    },
                )

            if step.order in seen_orders:
                return Result.fail(
                    "DUPLICATE_STEP_ORDER",
                    "Plan contains duplicate step orders.",
                    details={
                        "order": step.order,
                    },
                )

            seen_orders.add(step.order)

        expected_orders = set(
            range(
                1,
                len(plan.steps) + 1,
            )
        )

        if seen_orders != expected_orders:
            return Result.fail(
                "NON_SEQUENTIAL_STEP_ORDER",
                "Plan step orders must be sequential.",
                details={
                    "expected": sorted(
                        expected_orders
                    ),
                    "actual": sorted(
                        seen_orders
                    ),
                },
            )

        return Result.ok(plan)