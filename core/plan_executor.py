"""
Plan executor for AI Command Center.

Executes a validated ExecutionPlan sequentially through
the ActionExecutor.
"""

from __future__ import annotations

from core.action_executor import ActionExecutor
from core.pipeline_context import PipelineContext
from core.planner import ExecutionPlan
from core.result import Result


class PlanExecutor:
    """Execute all steps in an execution plan."""

    def __init__(
        self,
        action_executor: ActionExecutor,
    ) -> None:
        if not isinstance(
            action_executor,
            ActionExecutor,
        ):
            raise TypeError(
                "Expected an ActionExecutor instance."
            )

        self._action_executor = action_executor

    def execute(
        self,
        plan: ExecutionPlan,
        context: PipelineContext,
    ) -> Result[PipelineContext]:
        """Execute every plan step in order."""

        # -----------------------------------------------------
        # PLAN VALIDATION
        # -----------------------------------------------------

        if not isinstance(
            plan,
            ExecutionPlan,
        ):
            return Result.fail(
                "INVALID_EXECUTION_PLAN",
                "Expected an ExecutionPlan instance.",
            )

        # -----------------------------------------------------
        # CONTEXT VALIDATION
        # -----------------------------------------------------

        if not isinstance(
            context,
            PipelineContext,
        ):
            return Result.fail(
                "INVALID_PIPELINE_CONTEXT",
                "Expected a PipelineContext instance.",
            )

        # -----------------------------------------------------
        # EMPTY PLAN
        # -----------------------------------------------------

        if not plan.steps:
            return Result.fail(
                "EMPTY_EXECUTION_PLAN",
                "Execution plan contains no steps.",
            )

        # -----------------------------------------------------
        # STEP ORDER VALIDATION
        # -----------------------------------------------------

        previous_order = 0

        for step in plan.steps:
            if step.order <= previous_order:
                return Result.fail(
                    "INVALID_STEP_ORDER",
                    "Execution steps must be strictly ordered.",
                    details={
                        "step_id": step.step_id,
                        "step_name": step.name,
                        "step_order": step.order,
                    },
                )

            previous_order = step.order

        # -----------------------------------------------------
        # SEQUENTIAL EXECUTION
        # -----------------------------------------------------

        for step in plan.steps:
            try:
                result = self._action_executor.execute_step(
                    step,
                    context,
                )

            except Exception as exc:
                return Result.fail(
                    "PLAN_STEP_EXECUTION_ERROR",
                    str(exc),
                    details={
                        "step_id": step.step_id,
                        "step_name": step.name,
                        "action": step.action,
                        "exception_type": type(
                            exc
                        ).__name__,
                    },
                )

            # -------------------------------------------------
            # ACTION FAILURE
            # -------------------------------------------------

            if result.is_failure():
                return Result.fail(
                    result.error.code,
                    result.error.message,
                    details={
                        **result.error.details,
                        "failed_step": step.name,
                        "failed_step_id": step.step_id,
                    },
                )

            # -------------------------------------------------
            # OUTPUT
            # -------------------------------------------------

            context.set_output(
                result.data
            )

        return Result.ok(
            context
        )