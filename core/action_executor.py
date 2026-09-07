"""
Action executor for AI Command Center.

Resolves registered actions and executes them in a controlled
execution boundary.
"""

from __future__ import annotations

from typing import Any

from core.action_registry import ActionRegistry
from core.pipeline_context import PipelineContext
from core.planner import PlanStep
from core.result import Result


class ActionExecutor:
    """Execute plan actions through the ActionRegistry."""

    def __init__(
        self,
        registry: ActionRegistry,
    ) -> None:
        if not isinstance(
            registry,
            ActionRegistry,
        ):
            raise TypeError(
                "Expected an ActionRegistry instance."
            )

        self._registry = registry

    def execute_step(
        self,
        step: PlanStep,
        context: PipelineContext,
    ) -> Result[Any]:
        """Execute a single plan step."""

        # -----------------------------------------------------
        # STEP VALIDATION
        # -----------------------------------------------------

        if not isinstance(
            step,
            PlanStep,
        ):
            return Result.fail(
                "INVALID_PLAN_STEP",
                "Expected a PlanStep instance.",
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
        # STEP NAME VALIDATION
        # -----------------------------------------------------

        if not isinstance(
            step.name,
            str,
        ):
            return Result.fail(
                "INVALID_STEP_NAME",
                "Plan step name must be a string.",
                details={
                    "step_id": step.step_id,
                },
            )

        # -----------------------------------------------------
        # ACTION VALIDATION
        # -----------------------------------------------------

        if not isinstance(
            step.action,
            str,
        ):
            return Result.fail(
                "INVALID_ACTION",
                "Plan step action must be a string.",
                details={
                    "step_id": step.step_id,
                    "step_name": step.name,
                },
            )

        action_name = step.action.strip()

        if not action_name:
            return Result.fail(
                "INVALID_ACTION",
                "Plan step action cannot be empty.",
                details={
                    "step_id": step.step_id,
                    "step_name": step.name,
                },
            )

        # -----------------------------------------------------
        # APPROVAL GATE
        # -----------------------------------------------------

        if step.requires_approval:
            approved_step_id = context.get_metadata(
                "approved_step_id"
            )

            if approved_step_id != step.step_id:
                approval_error = {
                    "error": "Approval required before executing this step.",
                    "error_code": "APPROVAL_REQUIRED",
                }

                context.add_stage_result(
                    step.name,
                    approval_error,
                )

                context.set_metadata(
                    "execution_status",
                    "waiting_approval",
                )

                return Result.fail(
                    "APPROVAL_REQUIRED",
                    "Approval required before executing this step.",
                    details={
                        "step_id": step.step_id,
                        "step_name": step.name,
                        "action": action_name,
                    },
                )

        # -----------------------------------------------------
        # CURRENT STEP CONTEXT
        # -----------------------------------------------------
        #
        # Actions such as write_file consume the normalized
        # current step from PipelineContext metadata.
        # -----------------------------------------------------

        context.set_metadata(
            "current_step",
            {
                "step_id": step.step_id,
                "name": step.name,
                "description": step.description,
                "action": action_name,
                "requires_approval": step.requires_approval,
                "metadata": dict(step.metadata),
            },
        )

        # -----------------------------------------------------
        # RESOLVE ACTION
        # -----------------------------------------------------

        handler_result = self._registry.get(
            action_name
        )

        if handler_result.is_failure():
            return Result.fail(
                handler_result.error.code,
                handler_result.error.message,
                details={
                    **handler_result.error.details,
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "action": action_name,
                },
            )

        handler = handler_result.require_data()

        # -----------------------------------------------------
        # EXECUTE ACTION
        # -----------------------------------------------------

        try:
            result = handler(
                context
            )

        except Exception as exc:
            error_message = str(exc)

            context.add_stage_result(
                step.name,
                {
                    "error": error_message,
                    "error_code": "ACTION_EXECUTION_ERROR",
                },
            )

            return Result.fail(
                "ACTION_EXECUTION_ERROR",
                error_message,
                details={
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "action": action_name,
                    "exception_type": type(
                        exc
                    ).__name__,
                },
            )

        # -----------------------------------------------------
        # RESULT VALIDATION
        # -----------------------------------------------------

        if not isinstance(
            result,
            Result,
        ):
            error_message = (
                f"Action '{action_name}' must "
                "return a Result instance."
            )

            context.add_stage_result(
                step.name,
                {
                    "error": error_message,
                    "error_code": "INVALID_ACTION_RESULT",
                },
            )

            return Result.fail(
                "INVALID_ACTION_RESULT",
                error_message,
                details={
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "action": action_name,
                },
            )

        # -----------------------------------------------------
        # SUCCESS
        # -----------------------------------------------------

        if result.is_success():
            context.add_stage_result(
                step.name,
                result.data,
            )

            return Result.ok(
                result.data
            )

        # -----------------------------------------------------
        # ACTION-LEVEL FAILURE
        # -----------------------------------------------------

        error_message = (
            result.error.message
            if result.error
            else "Action failed."
        )

        error_code = (
            result.error.code
            if result.error
            else "ACTION_FAILED"
        )

        context.add_stage_result(
            step.name,
            {
                "error": error_message,
            },
        )

        return Result.fail(
            error_code,
            error_message,
            details={
                **(
                    result.error.details
                    if result.error
                    else {}
                ),
                "step_id": step.step_id,
                "step_name": step.name,
                "action": action_name,
            },
        )
