"""
Planning pipeline for AI Command Center.

Coordinates request normalization, plan construction,
and plan validation before execution.
"""

from __future__ import annotations

from core.plan_builder import PlanBuilder
from core.plan_validator import PlanValidator
from core.planner import ExecutionPlan
from core.result import Result


class PlanningPipeline:
    """Build and validate execution plans."""

    def __init__(
        self,
        validator: PlanValidator | None = None,
    ) -> None:
        self._validator = (
            validator
            if validator is not None
            else PlanValidator()
        )

    def create_plan(
        self,
        *,
        request: str,
        steps: list[dict[str, object]],
    ) -> Result[ExecutionPlan]:
        """
        Build and validate an execution plan.

        Each step dictionary must contain:
        - name
        - description
        - action

        Optional fields:
        - requires_approval
        - metadata
        """

        normalized_request = request.strip()

        if not normalized_request:
            return Result.fail(
                "EMPTY_REQUEST",
                "Planning request cannot be empty.",
            )

        if not steps:
            return Result.fail(
                "EMPTY_PLAN",
                "Planning requires at least one step.",
            )

        try:
            builder = PlanBuilder(
                normalized_request
            )

            for index, step in enumerate(
                steps,
                start=1,
            ):
                if not isinstance(
                    step,
                    dict,
                ):
                    return Result.fail(
                        "INVALID_STEP",
                        "Each planning step must be a dictionary.",
                        details={
                            "step_index": index,
                        },
                    )

                name = step.get("name")
                description = step.get(
                    "description"
                )
                action = step.get("action")

                if not isinstance(name, str):
                    return Result.fail(
                        "INVALID_STEP_NAME",
                        "Step name must be a string.",
                        details={
                            "step_index": index,
                        },
                    )

                if not isinstance(
                    description,
                    str,
                ):
                    return Result.fail(
                        "INVALID_STEP_DESCRIPTION",
                        "Step description must be a string.",
                        details={
                            "step_index": index,
                        },
                    )

                if not isinstance(action, str):
                    return Result.fail(
                        "INVALID_STEP_ACTION",
                        "Step action must be a string.",
                        details={
                            "step_index": index,
                        },
                    )

                requires_approval = step.get(
                    "requires_approval",
                    False,
                )

                if not isinstance(
                    requires_approval,
                    bool,
                ):
                    return Result.fail(
                        "INVALID_APPROVAL_FLAG",
                        "requires_approval must be boolean.",
                        details={
                            "step_index": index,
                        },
                    )

                metadata = step.get(
                    "metadata",
                    {},
                )

                if not isinstance(
                    metadata,
                    dict,
                ):
                    return Result.fail(
                        "INVALID_STEP_METADATA",
                        "Step metadata must be a dictionary.",
                        details={
                            "step_index": index,
                        },
                    )

                builder.add_step(
                    name=name,
                    description=description,
                    action=action,
                    requires_approval=(
                        requires_approval
                    ),
                    metadata=dict(metadata),
                )

            built = builder.build()

            if built.is_failure():
                return Result.fail(
                    built.error.code,
                    built.error.message,
                    details=built.error.details,
                )

            plan = built.require_data()

            validated = self._validator.validate(
                plan
            )

            if validated.is_failure():
                return Result.fail(
                    validated.error.code,
                    validated.error.message,
                    details=validated.error.details,
                )

            return Result.ok(
                validated.require_data()
            )

        except ValueError as exc:
            return Result.fail(
                "PLAN_BUILD_ERROR",
                str(exc),
            )
        except Exception as exc:
            return Result.fail(
                "PLANNING_PIPELINE_ERROR",
                str(exc),
                details={
                    "exception_type": type(
                        exc
                    ).__name__,
                },
            )