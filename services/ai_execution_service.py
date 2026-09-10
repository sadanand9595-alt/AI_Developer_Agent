"""High-level bridge from natural-language requests to execution."""

from __future__ import annotations

from uuid import uuid4

from ai.planner import AIPlanner
from config.settings import get_settings
from core.execution_system import ExecutionSystem
from core.pipeline_context import PipelineContext
from core.result import Result
from services.approval_service import ApprovalService


class AIExecutionService:
    """Plan a user request with AI and execute it through the core system."""

    def __init__(
        self,
        planner: AIPlanner,
        execution_system: ExecutionSystem,
        approval_service: ApprovalService | None = None,
    ) -> None:
        if not isinstance(planner, AIPlanner):
            raise TypeError("Expected an AIPlanner instance.")

        if not isinstance(execution_system, ExecutionSystem):
            raise TypeError("Expected an ExecutionSystem instance.")

        self._planner = planner
        self._execution_system = execution_system
        self._approval_service = approval_service

    def execute(
        self,
        request: str,
        *,
        context: PipelineContext | None = None,
        approval_service: ApprovalService | None = None,
    ) -> Result[PipelineContext]:
        """Create an AI plan and execute it through the existing lifecycle."""

        if not isinstance(request, str):
            return Result.fail(
                "INVALID_AI_EXECUTION_REQUEST",
                "AI execution request must be a string.",
            )

        normalized_request = request.strip()
        if not normalized_request:
            return Result.fail(
                "EMPTY_AI_EXECUTION_REQUEST",
                "AI execution request cannot be empty.",
            )

        pipeline_context = context or PipelineContext()
        if not isinstance(pipeline_context, PipelineContext):
            return Result.fail(
                "INVALID_PIPELINE_CONTEXT",
                "Expected a PipelineContext instance.",
            )

        pipeline_context.set_input(normalized_request)
        pipeline_context.set_metadata("request", normalized_request)

        plan_result = self._planner.create_plan(normalized_request)
        if plan_result.is_failure():
            return Result.fail(
                plan_result.error.code,
                plan_result.error.message,
                details=plan_result.error.details,
            )

        result = self._execution_system.execute(
            request=normalized_request,
            steps=plan_result.require_data(),
            context=pipeline_context,
        )
        return self._handle_approval(
            result,
            pipeline_context,
            approval_service,
            plan_steps=plan_result.require_data(),
        )

    def execute_agent(
        self,
        request: str,
        *,
        context: PipelineContext | None = None,
        max_iterations: int | None = None,
        approval_service: ApprovalService | None = None,
    ) -> Result[PipelineContext]:
        """Run a bounded plan/execute/observe agent loop."""

        if not isinstance(request, str):
            return Result.fail(
                "INVALID_AI_EXECUTION_REQUEST",
                "AI execution request must be a string.",
            )

        normalized_request = request.strip()
        if not normalized_request:
            return Result.fail(
                "EMPTY_AI_EXECUTION_REQUEST",
                "AI execution request cannot be empty.",
            )

        iteration_limit = (
            get_settings().max_agent_iterations
            if max_iterations is None
            else max_iterations
        )
        if not isinstance(iteration_limit, int) or isinstance(
            iteration_limit, bool
        ) or iteration_limit < 1:
            return Result.fail(
                "INVALID_MAX_ITERATIONS",
                "max_iterations must be a positive integer.",
            )

        root_context = context or PipelineContext()
        if not isinstance(root_context, PipelineContext):
            return Result.fail(
                "INVALID_PIPELINE_CONTEXT",
                "Expected a PipelineContext instance.",
            )

        root_context.set_input(normalized_request)
        root_context.set_metadata("request", normalized_request)
        root_context.set_metadata("iteration", 0)
        root_context.set_metadata("max_iterations", iteration_limit)
        root_context.set_metadata("execution_status", "running")
        root_context.set_metadata("plan_ids", [])

        for iteration in range(1, iteration_limit + 1):
            if root_context.get_metadata("cancel_requested") is True:
                root_context.set_metadata("execution_status", "cancelled")
                return Result.fail(
                    "EXECUTION_CANCELLED",
                    "AI execution was cancelled.",
                    details={"execution_id": root_context.execution_id},
                )

            plan_result = self._planner.create_plan(normalized_request)
            if plan_result.is_failure():
                root_context.set_metadata("execution_status", "failed")
                return Result.fail(
                    plan_result.error.code,
                    plan_result.error.message,
                    details={
                        **plan_result.error.details,
                        "execution_id": root_context.execution_id,
                        "iteration": iteration,
                    },
                )

            steps = plan_result.require_data()
            iteration_context = root_context
            if iteration > 1:
                iteration_context = PipelineContext(
                    execution_id=str(uuid4()),
                    task_id=root_context.task_id,
                    user_id=root_context.user_id,
                    agent_id=root_context.agent_id,
                    metadata=dict(root_context.metadata),
                )
                iteration_context.set_input(normalized_request)
                iteration_context.set_metadata(
                    "request",
                    normalized_request,
                )

            iteration_context.set_metadata("iteration", iteration)
            execution_result = self._execution_system.execute(
                request=normalized_request,
                steps=steps,
                context=iteration_context,
            )

            if execution_result.is_failure():
                approval_result = self._handle_approval(
                    execution_result,
                    root_context,
                    approval_service,
                    plan_steps=steps,
                )
                if approval_result.error and (
                    approval_result.error.code == "APPROVAL_REQUIRED"
                ):
                    return approval_result
                root_context.set_metadata("execution_status", "failed")
                return Result.fail(
                    approval_result.error.code,
                    approval_result.error.message,
                    details={
                        **approval_result.error.details,
                        "execution_id": root_context.execution_id,
                        "iteration": iteration,
                    },
                )

            completed_context = execution_result.require_data()
            root_context.metadata.update(completed_context.metadata)
            root_context.stage_results.update(completed_context.stage_results)
            root_context.set_output(completed_context.output_data)
            root_context.set_metadata("iteration", iteration)
            root_context.set_metadata(
                "last_plan_id",
                completed_context.get_metadata("plan_id"),
            )
            plan_ids = root_context.get_metadata("plan_ids")
            if isinstance(plan_ids, list):
                plan_id = completed_context.get_metadata("plan_id")
                if isinstance(plan_id, str):
                    plan_ids.append(plan_id)

            if self._plan_is_complete(steps):
                root_context.set_metadata("execution_status", "completed")
                return Result.ok(root_context)

        root_context.set_metadata("execution_status", "failed")
        return Result.fail(
            "AGENT_ITERATION_LIMIT",
            "AI execution reached the maximum iteration limit.",
            details={
                "execution_id": root_context.execution_id,
                "iteration": iteration_limit,
                "max_iterations": iteration_limit,
            },
        )

    @staticmethod
    def _plan_is_complete(steps: list[dict[str, object]]) -> bool:
        """Read the planner's explicit completion marker safely."""

        markers = [
            step.get(
                "objective_complete",
                step.get("metadata", {}).get("objective_complete")
                if isinstance(step.get("metadata"), dict)
                else None,
            )
            for step in steps
            if isinstance(step, dict)
        ]
        explicit_markers = [marker for marker in markers if isinstance(marker, bool)]
        return not explicit_markers or explicit_markers[-1] is True

    def _handle_approval(
        self,
        result: Result[PipelineContext],
        context: PipelineContext,
        approval_service: ApprovalService | None,
        plan_steps: list[dict[str, object]] | None = None,
    ) -> Result[PipelineContext]:
        """Persist an approval request when execution is paused."""

        if result.is_success() or result.error.code != "APPROVAL_REQUIRED":
            return result
        if approval_service is None:
            approval_service = self._approval_service
        if approval_service is None or not context.user_id:
            return Result.fail(
                "APPROVAL_PERSISTENCE_UNAVAILABLE",
                "Approval storage is required for approval-gated execution.",
                details=result.error.details,
            )

        details = result.error.details
        approval = approval_service.request_approval(
            user_id=context.user_id,
            action=str(details.get("action", "unknown")),
            reason=result.error.message,
            requested_operation=str(
                details.get("step_name", "Approval-gated execution")
            ),
            execution_id=context.execution_id,
            plan_id=self._optional_value(
                details.get("plan_id", context.get_metadata("plan_id"))
            ),
            step_id=str(details.get("step_id", "")),
            request_payload={
                "execution_snapshot": {
                    "execution_id": context.execution_id,
                    "plan": details.get("plan"),
                    "step_index": self._step_index(details, plan_steps),
                    "context": {
                        "task_id": context.task_id,
                        "user_id": context.user_id,
                        "agent_id": context.agent_id,
                        "input_data": context.input_data,
                        "output_data": context.output_data,
                        "metadata": dict(context.metadata),
                        "stage_results": dict(context.stage_results),
                    },
                },
            },
        )
        return Result.fail(
            "APPROVAL_REQUIRED",
            result.error.message,
            details={
                **details,
                "approval_id": approval.id,
                "execution_id": context.execution_id,
                "plan_id": context.get_metadata("plan_id"),
                "status": "waiting_approval",
            },
        )

    def resume_approved_execution(
        self,
        execution_id: str,
        approval_id: str,
        *,
        approval_service: ApprovalService | None = None,
    ) -> Result[PipelineContext]:
        """Validate and resume an approved execution."""

        service = approval_service or self._approval_service
        if service is None:
            return Result.fail(
                "APPROVAL_PERSISTENCE_UNAVAILABLE",
                "Approval storage is required to resume execution.",
            )
        approval = service.get_approval(approval_id)
        if approval is None or approval.execution_id != execution_id:
            return Result.fail(
                "APPROVAL_NOT_FOUND",
                "Approval request not found.",
            )
        if approval.status != "approved":
            return Result.fail(
                "APPROVAL_NOT_APPROVED",
                "Approval request is not approved.",
            )
        payload = approval.request_payload
        if self._execution_system.coordinator.get(execution_id) is None:
            if (
                not isinstance(payload, dict)
                or not isinstance(
                    payload.get("execution_snapshot"),
                    dict,
                )
            ):
                return Result.fail(
                    "INVALID_EXECUTION_SNAPSHOT",
                    "Approval does not contain execution recovery data.",
                )
            restored = self._execution_system.coordinator.restore_paused_execution(
                payload["execution_snapshot"]
            )
            if restored.is_failure():
                return Result.fail(
                    restored.error.code,
                    restored.error.message,
                    details=restored.error.details,
                )
        return self._execution_system.coordinator.resume_approved(
            execution_id,
            approval_id,
        )

    @staticmethod
    def _step_index(
        details: dict[str, object],
        plan_steps: list[dict[str, object]] | None,
    ) -> int:
        step_id = details.get("step_id")
        serialized_plan = details.get("plan")
        if isinstance(serialized_plan, dict):
            serialized_steps = serialized_plan.get("steps")
            if isinstance(serialized_steps, list):
                for index, step in enumerate(serialized_steps):
                    if (
                        isinstance(step, dict)
                        and step.get("step_id") == step_id
                    ):
                        return index
        if isinstance(plan_steps, list):
            for index, step in enumerate(plan_steps):
                if (
                    isinstance(step, dict)
                    and step.get("step_id") == step_id
                ):
                    return index
        return 0

    @staticmethod
    def _optional_value(value: object) -> str | None:
        return value if isinstance(value, str) else None

    def cancel_execution(
        self,
        execution_id: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> Result[PipelineContext]:
        """Cancel a running execution through the core execution system."""

        if not isinstance(execution_id, str):
            return Result.fail(
                "INVALID_EXECUTION_ID",
                "Execution ID must be a string.",
            )

        normalized_execution_id = execution_id.strip()

        if not normalized_execution_id:
            return Result.fail(
                "INVALID_EXECUTION_ID",
                "Execution ID cannot be empty.",
            )

        record = self._execution_system.cancel(
            normalized_execution_id,
            metadata=metadata,
        )

        if record.status == "cancelled":
            return Result.fail(
                "EXECUTION_CANCELLED",
                "AI execution was cancelled.",
                details={
                    "execution_id": normalized_execution_id,
                    "task_id": record.task_id,
                },
            )

        return Result.fail(
            "EXECUTION_CANCELLATION_FAILED",
            "AI execution could not be cancelled.",
            details={
                "execution_id": normalized_execution_id,
                "task_id": record.task_id,
                "status": record.status,
            },
        )
    def reject_execution(
        self,
        execution_id: str,
        approval_id: str,
        *,
        approval_service: ApprovalService | None = None,
    ) -> Result[PipelineContext]:
        """Terminate an execution after approval rejection."""

        service = approval_service or self._approval_service
        if service is None:
            return Result.fail(
                "APPROVAL_PERSISTENCE_UNAVAILABLE",
                "Approval storage is required to reject execution.",
            )
        approval = service.get_approval(approval_id)
        if approval is None or approval.execution_id != execution_id:
            return Result.fail("APPROVAL_NOT_FOUND", "Approval request not found.")
        if approval.status != "rejected":
            return Result.fail("APPROVAL_NOT_REJECTED", "Approval is not rejected.")
        self._execution_system.cancel(
            execution_id,
            metadata={"approval_id": approval_id, "rejected": True},
        )
        return Result.fail(
            "APPROVAL_REJECTED",
            "Execution was rejected by human approval.",
            details={"execution_id": execution_id, "approval_id": approval_id},
        )


__all__ = ["AIExecutionService"]
