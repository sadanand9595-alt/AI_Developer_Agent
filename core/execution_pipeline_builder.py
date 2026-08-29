"""
Execution pipeline builder for AI Command Center.

Provides a controlled builder API for assembling execution
pipelines from validated stages.
"""

from __future__ import annotations

from core.execution_pipeline import (
    ExecutionPipeline,
    PipelineStage,
)
from core.result import Result


class ExecutionPipelineBuilder:
    """Build an ordered ExecutionPipeline."""

    def __init__(self) -> None:
        self._pipeline = ExecutionPipeline()

    def add_stage(
        self,
        name: str,
        handler,
    ) -> "ExecutionPipelineBuilder":
        """Add a validated stage to the pipeline."""

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Pipeline stage name cannot be empty."
            )

        if not callable(handler):
            raise TypeError(
                f"Handler for stage '{normalized_name}' "
                "must be callable."
            )

        self._pipeline.add_stage(
            PipelineStage(
                name=normalized_name,
                handler=handler,
            )
        )

        return self

    def add_passthrough_stage(
        self,
        name: str,
    ) -> "ExecutionPipelineBuilder":
        """Add a stage that passes its value unchanged."""

        return self.add_stage(
            name,
            lambda value: Result.ok(value),
        )

    def stage_count(self) -> int:
        """Return the number of configured stages."""

        return self._pipeline.stage_count()

    def stage_names(self) -> tuple[str, ...]:
        """Return configured stage names."""

        return self._pipeline.stage_names()

    def build(self) -> ExecutionPipeline:
        """Return the configured execution pipeline."""

        return self._pipeline

    def reset(self) -> "ExecutionPipelineBuilder":
        """Remove all configured stages."""

        self._pipeline.clear()

        return self