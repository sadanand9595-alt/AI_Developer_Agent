"""
Execution engine for AI Command Center.

Provides the runtime boundary for executing planned work
through the ExecutionCoordinator.
"""

from __future__ import annotations

from core.action_registry import ActionRegistry
from core.execution_coordinator import ExecutionCoordinator
from core.pipeline_context import PipelineContext
from core.planner import ExecutionPlan
from core.result import Result


class ExecutionEngine:
    """High-level execution engine."""

    def __init__(
        self,
        registry: ActionRegistry,
        coordinator: ExecutionCoordinator | None = None,
    ) -> None:
        self._registry = registry

        self._coordinator = (
            coordinator
            if coordinator is not None
            else ExecutionCoordinator(
                registry
            )
        )

    def execute(
        self,
        *,
        request: str,
        steps: list[dict[str, object]],
        context: PipelineContext,
    ) -> Result[PipelineContext]:
        """
        Create and execute a plan from a user request.
        """

        if not isinstance(
            request,
            str,
        ):
            return Result.fail(
                "INVALID_REQUEST",
                "Expected request to be a string.",
            )

        if not isinstance(
            context,
            PipelineContext,
        ):
            return Result.fail(
                "INVALID_PIPELINE_CONTEXT",
                "Expected a PipelineContext instance.",
            )

        return self._coordinator.execute(
            request=request,
            steps=steps,
            context=context,
        )

    def execute_plan(
        self,
        *,
        plan: ExecutionPlan,
        context: PipelineContext,
    ) -> Result[PipelineContext]:
        """Execute an already-created execution plan."""

        if not isinstance(
            plan,
            ExecutionPlan,
        ):
            return Result.fail(
                "INVALID_EXECUTION_PLAN",
                "Expected an ExecutionPlan instance.",
            )

        if not isinstance(
            context,
            PipelineContext,
        ):
            return Result.fail(
                "INVALID_PIPELINE_CONTEXT",
                "Expected a PipelineContext instance.",
            )

        return self._coordinator.execute_plan(
            plan=plan,
            context=context,
        )

    @property
    def coordinator(
        self,
    ) -> ExecutionCoordinator:
        """Return the execution coordinator."""

        return self._coordinator

    @property
    def registry(
        self,
    ) -> ActionRegistry:
        """Return the action registry."""

        return self._registry