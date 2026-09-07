"""
Execution coordinator for AI Command Center.

Central orchestration boundary for:

- Planning
- Plan validation
- Plan execution
- Action execution
- Execution lifecycle
- Execution registration
- Execution runtime
- Execution context runtime
- Progress tracking
- Observation
- Audit access
"""

from __future__ import annotations

from dataclasses import dataclass

from core.action_executor import ActionExecutor
from core.action_registry import ActionRegistry
from core.execution_context_runtime_application import (
    ExecutionContextRuntimeApplication,
)
from core.execution_facade import ExecutionFacade
from core.execution_manager import ExecutionRecord
from core.execution_registry import ExecutionRegistry
from core.execution_registry_service import (
    ExecutionRegistryService,
)
from core.execution_tracker import ExecutionProgress
from core.plan_executor import PlanExecutor
from core.planning_pipeline import PlanningPipeline
from core.planner import ExecutionPlan, PlanStep
from core.pipeline_context import PipelineContext
from core.result import Result


@dataclass(slots=True)
class _PausedExecution:
    plan: ExecutionPlan
    context: PipelineContext
    step_index: int


class ExecutionCoordinator:
    """
    Central orchestration boundary for execution.

    Coordinates the complete execution lifecycle:

        Request
            ↓
        PlanningPipeline
            ↓
        ExecutionPlan
            ↓
        PlanExecutor
            ↓
        ActionExecutor
            ↓
        ActionRegistry

    Runtime synchronization:

        ExecutionCoordinator
            ├── ExecutionFacade
            ├── ExecutionRegistryService
            └── ExecutionContextRuntimeApplication
    """

    def __init__(
        self,
        registry: ActionRegistry | None = None,
        facade: ExecutionFacade | None = None,
        registry_service: ExecutionRegistryService | None = None,
        planning_pipeline: PlanningPipeline | None = None,
        plan_executor: PlanExecutor | None = None,
        runtime_application: (
            ExecutionContextRuntimeApplication | None
        ) = None,
    ) -> None:
        """
        Initialize the execution coordinator.
        """

        if registry is not None and not isinstance(
            registry,
            ActionRegistry,
        ):
            raise TypeError(
                "Expected an ActionRegistry instance."
            )

        if facade is not None and not isinstance(
            facade,
            ExecutionFacade,
        ):
            raise TypeError(
                "Expected an ExecutionFacade instance."
            )

        if registry_service is not None and not isinstance(
            registry_service,
            ExecutionRegistryService,
        ):
            raise TypeError(
                "Expected an ExecutionRegistryService instance."
            )

        if planning_pipeline is not None and not isinstance(
            planning_pipeline,
            PlanningPipeline,
        ):
            raise TypeError(
                "Expected a PlanningPipeline instance."
            )

        if plan_executor is not None and not isinstance(
            plan_executor,
            PlanExecutor,
        ):
            raise TypeError(
                "Expected a PlanExecutor instance."
            )

        if runtime_application is not None and not isinstance(
            runtime_application,
            ExecutionContextRuntimeApplication,
        ):
            raise TypeError(
                "Expected an ExecutionContextRuntimeApplication "
                "instance."
            )

        # -----------------------------------------------------
        # ACTION REGISTRY
        # -----------------------------------------------------

        self._registry = (
            registry
            if registry is not None
            else ActionRegistry()
        )

        # -----------------------------------------------------
        # EXECUTION FACADE
        # -----------------------------------------------------

        self._facade = (
            facade
            if facade is not None
            else ExecutionFacade()
        )

        # -----------------------------------------------------
        # EXECUTION REGISTRY
        # -----------------------------------------------------

        self._registry_service = (
            registry_service
            if registry_service is not None
            else ExecutionRegistryService(
                ExecutionRegistry()
            )
        )

        # -----------------------------------------------------
        # PLANNING
        # -----------------------------------------------------

        self._planning_pipeline = (
            planning_pipeline
            if planning_pipeline is not None
            else PlanningPipeline()
        )

        # -----------------------------------------------------
        # PLAN EXECUTION
        # -----------------------------------------------------

        self._plan_executor = (
            plan_executor
            if plan_executor is not None
            else PlanExecutor(
                ActionExecutor(
                    self._registry
                )
            )
        )

        # -----------------------------------------------------
        # EXECUTION CONTEXT RUNTIME
        # -----------------------------------------------------

        self._runtime_application = (
            runtime_application
            if runtime_application is not None
            else ExecutionContextRuntimeApplication()
        )
        self._paused: dict[str, _PausedExecution] = {}

    # =========================================================
    # MAIN EXECUTION API
    # =========================================================

    def execute(
        self,
        *,
        request: str,
        steps: list[dict[str, object]],
        context: PipelineContext,
    ) -> Result[PipelineContext]:
        """
        Build, validate, register, and execute an execution plan.
        """

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
        # CREATE PLAN
        # -----------------------------------------------------

        planning_result = (
            self._planning_pipeline.create_plan(
                request=request,
                steps=steps,
            )
        )

        if planning_result.is_failure():
            return Result.fail(
                planning_result.error.code,
                planning_result.error.message,
                details=planning_result.error.details,
            )

        plan = planning_result.require_data()

        # -----------------------------------------------------
        # EXECUTE PLAN
        # -----------------------------------------------------

        return self.execute_plan(
            plan=plan,
            context=context,
        )

    def execute_plan(
        self,
        *,
        plan: ExecutionPlan,
        context: PipelineContext,
    ) -> Result[PipelineContext]:
        """
        Execute an already-created execution plan.
        """

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

        execution_id = context.execution_id
        total_steps = len(plan.steps)

        # -----------------------------------------------------
        # DUPLICATE EXECUTION PROTECTION
        # -----------------------------------------------------

        # -----------------------------------------------------
        # Duplicate detection covers both:
        #
        # - Executions currently registered (active).
        # - Executions with prior history in the execution
        #   manager that were never cleared (e.g. completed,
        #   failed, or cancelled executions reusing the same
        #   execution_id). ``is_registered`` alone cannot see
        #   these because the registry is unregistered on
        #   completion while the manager record persists.
        # -----------------------------------------------------

        if self.is_registered(
            execution_id
        ) or self.get(
            execution_id
        ) is not None:
            return Result.fail(
                "EXECUTION_ALREADY_REGISTERED",
                (
                    "Execution is already registered: "
                    f"{execution_id}"
                ),
            )

        # -----------------------------------------------------
        # CONTEXT METADATA
        # -----------------------------------------------------

        context.set_metadata(
            "plan_id",
            plan.plan_id,
        )

        context.set_metadata(
            "step_count",
            total_steps,
        )

        context.set_metadata(
            "execution_status",
            "running",
        )

        # -----------------------------------------------------
        # START EXECUTION
        # -----------------------------------------------------

        try:
            self.start(
                execution_id,
                task_id=context.task_id,
                total_steps=total_steps,
                metadata={
                    "plan_id": plan.plan_id,
                    "step_count": total_steps,
                },
            )

        except Exception as exc:
            context.set_metadata(
                "execution_status",
                "failed",
            )

            return Result.fail(
                "EXECUTION_START_ERROR",
                str(exc),
                details={
                    "execution_id": execution_id,
                    "exception_type": type(
                        exc
                    ).__name__,
                },
            )

        # -----------------------------------------------------
        # EXECUTE PLAN STEPS
        # -----------------------------------------------------

        try:
            result = self._execute_plan_steps(
                plan=plan,
                context=context,
            )

        except Exception as exc:
            self._cleanup_failed_execution(
                execution_id=execution_id,
                error_code="EXECUTION_ERROR",
                error_message=str(exc),
            )

            context.set_metadata(
                "execution_status",
                "failed",
            )

            return Result.fail(
                "EXECUTION_ERROR",
                str(exc),
                details={
                    "execution_id": execution_id,
                    "exception_type": type(
                        exc
                    ).__name__,
                },
            )

        # -----------------------------------------------------
        # PLAN EXECUTION FAILURE
        # -----------------------------------------------------

        if result.is_failure():
            if result.error.code == "APPROVAL_REQUIRED":
                step_index = next(
                    (
                        index
                        for index, step in enumerate(plan.steps)
                        if step.step_id
                        == result.error.details.get("step_id")
                    ),
                    0,
                )
                self._paused[execution_id] = _PausedExecution(
                    plan=plan,
                    context=context,
                    step_index=step_index,
                )
                self._facade.wait_for_approval(
                    execution_id,
                    metadata={
                        "plan_id": plan.plan_id,
                        "approval": result.error.details,
                    },
                )
                context.set_metadata(
                    "execution_status",
                    "waiting_approval",
                )
                return Result.fail(
                    result.error.code,
                    result.error.message,
                    details={
                        **result.error.details,
                        "execution_id": execution_id,
                        "plan_id": plan.plan_id,
                        "status": "waiting_approval",
                        "plan": self._serialize_plan(plan),
                    },
                )

            error_code = result.error.code
            error_message = result.error.message

            self._cleanup_failed_execution(
                execution_id=execution_id,
                error_code=error_code,
                error_message=error_message,
            )

            context.set_metadata(
                "execution_status",
                "failed",
            )

            return Result.fail(
                error_code,
                error_message,
                details={
                    **result.error.details,
                    "execution_id": execution_id,
                },
            )

        final_context = result.require_data()

        # -----------------------------------------------------
        # FINAL EXECUTION COMPLETION
        # -----------------------------------------------------
        #
        # IMPORTANT:
        #
        # When the final step is completed, ExecutionRuntime
        # can already transition ExecutionManager into the
        # "completed" state.
        #
        # Therefore we MUST NOT blindly call complete()
        # again.
        #
        # -----------------------------------------------------

        try:
            record = self.get(
                execution_id
            )

            if record is None:
                # The execution may already have been
                # completed and removed from the registry.
                #
                # This is acceptable because the lifecycle
                # runtime may already have finalized it.
                pass

            elif record.status == "running":
                self.complete(
                    execution_id,
                    output=final_context.output_data,
                    metadata={
                        "plan_id": plan.plan_id,
                        "step_count": total_steps,
                    },
                )

            elif record.status == "completed":
                # Final step already completed the execution.
                #
                # DO NOT call self.complete() again.
                self._cleanup_completed_runtime(
                    execution_id
                )

            elif record.status in {
                "failed",
                "cancelled",
            }:
                return Result.fail(
                    "UNEXPECTED_EXECUTION_STATUS",
                    (
                        "Execution reached an unexpected "
                        f"terminal state: {record.status}"
                    ),
                    details={
                        "execution_id": execution_id,
                        "status": record.status,
                    },
                )

            else:
                return Result.fail(
                    "UNKNOWN_EXECUTION_STATUS",
                    (
                        "Execution has an unknown status: "
                        f"{record.status}"
                    ),
                    details={
                        "execution_id": execution_id,
                        "status": record.status,
                    },
                )

        except Exception as exc:
            context.set_metadata(
                "execution_status",
                "failed",
            )

            return Result.fail(
                "EXECUTION_COMPLETION_ERROR",
                str(exc),
                details={
                    "execution_id": execution_id,
                    "exception_type": type(
                        exc
                    ).__name__,
                },
            )

        # -----------------------------------------------------
        # FINAL CONTEXT STATE
        # -----------------------------------------------------

        final_context.set_metadata(
            "execution_status",
            "completed",
        )

        return Result.ok(
            final_context
        )

    def restore_paused_execution(
        self,
        snapshot: dict[str, object],
    ) -> Result[None]:
        """Restore a persisted approval-paused execution."""

        if not isinstance(snapshot, dict):
            return Result.fail(
                "INVALID_EXECUTION_SNAPSHOT",
                "Execution snapshot must be an object.",
            )

        execution_id = snapshot.get("execution_id")
        plan_data = snapshot.get("plan")
        context_data = snapshot.get("context")
        step_index = snapshot.get("step_index")

        if not isinstance(execution_id, str) or not execution_id.strip():
            return Result.fail(
                "INVALID_EXECUTION_SNAPSHOT",
                "Execution snapshot has no valid execution ID.",
            )
        if not isinstance(plan_data, dict):
            return Result.fail(
                "INVALID_EXECUTION_SNAPSHOT",
                "Execution snapshot has no valid plan.",
            )
        if not isinstance(context_data, dict):
            return Result.fail(
                "INVALID_EXECUTION_SNAPSHOT",
                "Execution snapshot has no valid context.",
            )
        if (
            not isinstance(step_index, int)
            or isinstance(step_index, bool)
            or step_index < 0
        ):
            return Result.fail(
                "INVALID_EXECUTION_SNAPSHOT",
                "Execution snapshot has no valid step index.",
            )

        try:
            plan = self._deserialize_plan(plan_data)
            context = PipelineContext(
                execution_id=execution_id,
                task_id=self._optional_string(
                    context_data.get("task_id")
                ),
                user_id=self._optional_string(
                    context_data.get("user_id")
                ),
                agent_id=self._optional_string(
                    context_data.get("agent_id")
                ),
                input_data=context_data.get("input_data"),
                output_data=context_data.get("output_data"),
                metadata=self._dict_value(
                    context_data.get("metadata")
                ),
                stage_results=self._dict_value(
                    context_data.get("stage_results")
                ),
            )
        except ValueError as exc:
            return Result.fail(
                "INVALID_EXECUTION_SNAPSHOT",
                str(exc),
            )

        if step_index >= len(plan.steps):
            return Result.fail(
                "INVALID_EXECUTION_SNAPSHOT",
                "Execution snapshot step index is out of range.",
            )

        if self._paused.get(execution_id) is not None:
            return Result.ok()

        if self.get(execution_id) is not None:
            return Result.fail(
                "EXECUTION_ALREADY_REGISTERED",
                "Execution already exists in this coordinator.",
            )

        try:
            self.start(
                execution_id,
                task_id=context.task_id,
                total_steps=len(plan.steps),
                metadata={"plan_id": plan.plan_id},
            )
            self._facade.wait_for_approval(
                execution_id,
                metadata={
                    "plan_id": plan.plan_id,
                    "status": "waiting_approval",
                },
            )
        except (KeyError, ValueError) as exc:
            return Result.fail(
                "EXECUTION_RESTORE_ERROR",
                str(exc),
                details={"execution_id": execution_id},
            )

        context.set_metadata("execution_status", "waiting_approval")
        self._paused[execution_id] = _PausedExecution(
            plan=plan,
            context=context,
            step_index=step_index,
        )
        return Result.ok()

    def resume_approved(
        self,
        execution_id: str,
        approval_id: str,
    ) -> Result[PipelineContext]:
        """Resume a paused execution from its blocked step."""

        paused = self._paused.get(execution_id)
        if paused is None:
            return Result.fail(
                "EXECUTION_NOT_WAITING_APPROVAL",
                "Execution is not waiting for approval.",
            )
        if not isinstance(approval_id, str) or not approval_id.strip():
            return Result.fail(
                "INVALID_APPROVAL_ID",
                "Approval ID cannot be empty.",
            )
        paused.context.set_metadata(
            "approved_step_id",
            paused.plan.steps[paused.step_index].step_id,
        )

        result = self._execute_plan_steps(
            plan=paused.plan,
            context=paused.context,
            start_index=paused.step_index,
            resume_first=True,
        )
        if result.is_failure():
            return Result.fail(
                result.error.code,
                result.error.message,
                details={
                    **result.error.details,
                    "execution_id": execution_id,
                    "plan_id": paused.plan.plan_id,
                },
            )

        final_context = result.require_data()
        record = self.get(execution_id)
        if record is not None and record.status == "running":
            self.complete(
                execution_id,
                output=final_context.output_data,
                metadata={"plan_id": paused.plan.plan_id},
            )
        elif record is not None and record.status == "completed":
            self._cleanup_completed_runtime(execution_id)
        self._paused.pop(execution_id, None)
        final_context.set_metadata("execution_status", "completed")
        return Result.ok(final_context)

    # =========================================================
    # PLAN STEP EXECUTION
    # =========================================================

    def _execute_plan_steps(
        self,
        *,
        plan: ExecutionPlan,
        context: PipelineContext,
        start_index: int = 0,
        resume_first: bool = False,
    ) -> Result[PipelineContext]:
        """
        Execute plan steps sequentially.

        Each step is synchronized with:

        - ExecutionFacade
        - ExecutionContextRuntimeApplication
        - PlanExecutor
        """

        current_context = context

        for index, step in enumerate(plan.steps):
            if index < start_index:
                continue
            execution_id = (
                current_context.execution_id
            )

            # -------------------------------------------------
            # START STEP
            # -------------------------------------------------

            try:
                self.start_step(
                    execution_id,
                    step.name,
                    task_id=current_context.task_id,
                )

            except Exception as exc:
                return Result.fail(
                    "STEP_START_ERROR",
                    str(exc),
                    details={
                        "step_id": step.step_id,
                        "step_name": step.name,
                    },
                )

            # -------------------------------------------------
            # SINGLE-STEP PLAN
            # -------------------------------------------------
            #
            # PlanExecutor is intentionally used for each
            # individual step so the coordinator remains the
            # lifecycle boundary.
            #
            # -------------------------------------------------

            single_step_plan = ExecutionPlan(
                plan_id=plan.plan_id,
                request=plan.request,
                steps=(step,),
                metadata=dict(
                    plan.metadata
                ),
            )

            # -------------------------------------------------
            # EXECUTE ACTION
            # -------------------------------------------------

            result = self._plan_executor.execute(
                single_step_plan,
                current_context,
            )

            if result.is_failure():
                return Result.fail(
                    result.error.code,
                    result.error.message,
                    details={
                        **result.error.details,
                        "step_id": step.step_id,
                        "step_name": step.name,
                    },
                )

            current_context = (
                result.require_data()
            )

            # -------------------------------------------------
            # COMPLETE STEP
            # -------------------------------------------------

            try:
                self.complete_step(
                    execution_id,
                    step.name,
                    task_id=current_context.task_id,
                )

            except Exception as exc:
                return Result.fail(
                    "STEP_COMPLETION_ERROR",
                    str(exc),
                    details={
                        "step_id": step.step_id,
                        "step_name": step.name,
                    },
                )

        return Result.ok(
            current_context
        )

    @staticmethod
    def _serialize_plan(
        plan: ExecutionPlan,
    ) -> dict[str, object]:
        """Serialize a validated plan for approval recovery."""

        return {
            "plan_id": plan.plan_id,
            "request": plan.request,
            "metadata": dict(plan.metadata),
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "description": step.description,
                    "action": step.action,
                    "order": step.order,
                    "requires_approval": step.requires_approval,
                    "metadata": dict(step.metadata),
                }
                for step in plan.steps
            ],
        }

    @staticmethod
    def _deserialize_plan(
        data: dict[str, object],
    ) -> ExecutionPlan:
        """Validate and reconstruct a persisted execution plan."""

        plan_id = data.get("plan_id")
        request = data.get("request")
        raw_steps = data.get("steps")
        if (
            not isinstance(plan_id, str)
            or not plan_id.strip()
            or not isinstance(request, str)
            or not request.strip()
            or not isinstance(raw_steps, list)
            or not raw_steps
        ):
            raise ValueError("Execution snapshot plan is invalid.")

        steps = []
        for raw_step in raw_steps:
            if not isinstance(raw_step, dict):
                raise ValueError("Execution snapshot step is invalid.")
            required = (
                "step_id",
                "name",
                "description",
                "action",
                "order",
            )
            if any(
                not isinstance(raw_step.get(key), str)
                for key in required[:4]
            ) or not isinstance(raw_step.get("order"), int):
                raise ValueError("Execution snapshot step is invalid.")
            metadata = raw_step.get("metadata", {})
            requires_approval = raw_step.get(
                "requires_approval",
                False,
            )
            if not isinstance(metadata, dict) or not isinstance(
                requires_approval,
                bool,
            ):
                raise ValueError("Execution snapshot step is invalid.")
            steps.append(
                PlanStep(
                    step_id=raw_step["step_id"],
                    name=raw_step["name"],
                    description=raw_step["description"],
                    action=raw_step["action"],
                    order=raw_step["order"],
                    requires_approval=requires_approval,
                    metadata=dict(metadata),
                )
            )

        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("Execution snapshot plan is invalid.")
        return ExecutionPlan(
            plan_id=plan_id,
            request=request,
            steps=tuple(steps),
            metadata=dict(metadata),
        )

    @staticmethod
    def _dict_value(value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            return {}
        return dict(value)

    @staticmethod
    def _optional_string(value: object) -> str | None:
        return value if isinstance(value, str) else None

    # =========================================================
    # EXECUTION LIFECYCLE
    # =========================================================

    def start(
        self,
        execution_id: str,
        *,
        task_id: str | None = None,
        total_steps: int = 0,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """
        Start and register an execution.
        """

        record = self._facade.start(
            execution_id,
            task_id=task_id,
            total_steps=total_steps,
            metadata=metadata,
        )

        self._registry_service.register(
            execution_id,
            record,
        )

        self._runtime_application.create(
            execution_id
        )

        return record

    def start_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """
        Start an execution step.
        """

        progress = self._facade.start_step(
            execution_id,
            step_name,
            task_id=task_id,
        )

        if self._runtime_application.contains(
            execution_id
        ):
            self._runtime_application.start_step(
                execution_id,
                step_name,
            )

        return progress

    def complete_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """
        Complete an execution step.
        """

        progress = self._facade.complete_step(
            execution_id,
            step_name,
            task_id=task_id,
        )

        if self._runtime_application.contains(
            execution_id
        ):
            self._runtime_application.complete_step(
                execution_id
            )

        # -----------------------------------------------------
        # Cleanup when execution reaches 100%.
        #
        # Completing the final step can auto-transition the
        # execution to "completed" without complete() ever being
        # called. Only unregistering from the execution registry
        # here (and not the context runtime) leaves an active,
        # never-stopped ExecutionContextRuntime permanently
        # orphaned in _runtime_application for any caller using
        # the step API directly instead of execute_plan()/
        # complete(). Use the same cleanup as complete().
        # -----------------------------------------------------

        if progress.status == "completed":
            self._cleanup_completed_runtime(
                execution_id
            )

        return progress

    def complete(
        self,
        execution_id: str,
        *,
        output: object = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """
        Complete and unregister an execution.
        """

        record = self._facade.complete(
            execution_id,
            output=output,
            metadata=metadata,
        )

        self._cleanup_completed_runtime(
            execution_id
        )

        return record

    def fail(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        step_name: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """
        Fail and unregister an execution.
        """

        record = self._facade.fail(
            execution_id,
            error_code=error_code,
            error_message=error_message,
            step_name=step_name,
            metadata=metadata,
        )

        self._cleanup_failed_runtime(
            execution_id
        )

        return record

    def cancel(
        self,
        execution_id: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """
        Cancel and unregister an execution.
        """

        record = self._facade.cancel(
            execution_id,
            metadata=metadata,
        )

        self._cleanup_failed_runtime(
            execution_id
        )

        return record

    # =========================================================
    # EXECUTION STATE
    # =========================================================

    def get(
        self,
        execution_id: str,
    ) -> ExecutionRecord | None:
        """
        Get execution state.
        """

        return self._facade.get(
            execution_id
        )

    def get_progress(
        self,
        execution_id: str,
    ) -> ExecutionProgress | None:
        """
        Get execution progress.
        """

        return self._facade.get_progress(
            execution_id
        )

    def get_observation(
        self,
        execution_id: str,
    ):
        """
        Get execution observation.
        """

        return self._facade.get_observation(
            execution_id
        )

    def get_audit(
        self,
        execution_id: str,
    ):
        """
        Get execution audit records.
        """

        return self._facade.get_audit(
            execution_id
        )

    # =========================================================
    # REGISTRY
    # =========================================================

    def is_registered(
        self,
        execution_id: str,
    ) -> bool:
        """
        Return whether an execution is registered.
        """

        return self._registry_service.contains(
            execution_id
        )

    def registered_count(
        self,
    ) -> int:
        """
        Return number of registered executions.
        """

        return self._registry_service.count()

    def registered_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return all registered execution IDs.
        """

        return self._registry_service.ids()

    # =========================================================
    # MONITORING
    # =========================================================

    def active_count(
        self,
    ) -> int:
        """
        Return active execution count.
        """

        return self._facade.active_count()

    def audit_count(
        self,
    ) -> int:
        """
        Return total audit record count.
        """

        return self._facade.audit_count()

    # =========================================================
    # EXECUTION CONTEXT RUNTIME
    # =========================================================

    def get_runtime(
        self,
        execution_id: str,
    ):
        """
        Return the execution context runtime.
        """

        return self._runtime_application.get(
            execution_id
        )

    def get_runtime_snapshot(
        self,
        execution_id: str,
    ) -> dict[str, object]:
        """
        Return an execution context runtime snapshot.
        """

        return self._runtime_application.snapshot(
            execution_id
        )

    # =========================================================
    # CLEANUP HELPERS
    # =========================================================

    def _cleanup_completed_runtime(
        self,
        execution_id: str,
    ) -> None:
        """
        Cleanup context runtime after successful completion.
        """

        try:
            if self._runtime_application.contains(
                execution_id
            ):
                self._runtime_application.unregister(
                    execution_id,
                    stop=True,
                )
        finally:
            self._registry_service.unregister(
                execution_id
            )

    def _cleanup_failed_runtime(
        self,
        execution_id: str,
    ) -> None:
        """
        Cleanup context runtime after failure/cancellation.
        """

        try:
            if self._runtime_application.contains(
                execution_id
            ):
                self._runtime_application.unregister(
                    execution_id,
                    stop=True,
                )
        finally:
            self._registry_service.unregister(
                execution_id
            )

    def _cleanup_failed_execution(
        self,
        *,
        execution_id: str,
        error_code: str,
        error_message: str,
    ) -> None:
        """
        Best-effort cleanup after an execution failure.
        """

        try:
            record = self.get(
                execution_id
            )

            if (
                record is not None
                and record.status == "running"
            ):
                self.fail(
                    execution_id,
                    error_code=error_code,
                    error_message=error_message,
                )

        except Exception:
            pass

        try:
            self._cleanup_failed_runtime(
                execution_id
            )
        except Exception:
            pass

    # =========================================================
    # CLOSE
    # =========================================================

    def close(
        self,
    ) -> None:
        """
        Close all execution resources.
        """

        self._runtime_application.clear(
            stop=True
        )

        self._facade.close()

        self._registry_service.clear()


__all__ = [
    "ExecutionCoordinator",
]