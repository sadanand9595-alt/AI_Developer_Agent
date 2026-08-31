"""
Execution pipeline for AI Command Center.

Provides a controlled sequence of execution stages.

The pipeline is intentionally generic so that future
planner, executor, validator, and retry components can
be plugged into the same execution boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from core.result import Result


T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True, slots=True)
class PipelineStage(Generic[T, U]):
    """A single execution pipeline stage."""

    name: str
    handler: Callable[[T], Result[U]]

    def execute(
        self,
        value: T,
    ) -> Result[U]:
        """Execute this pipeline stage."""

        if not isinstance(self.name, str) or not self.name.strip():
            return Result.fail(
                "INVALID_STAGE_NAME",
                "Pipeline stage name cannot be empty.",
            )

        try:
            result = self.handler(value)

            if not isinstance(result, Result):
                return Result.fail(
                    "INVALID_STAGE_RESULT",
                    (
                        f"Stage '{self.name}' must return "
                        "a Result instance."
                    ),
                )

            return result

        except Exception as exc:
            return Result.fail(
                "PIPELINE_STAGE_ERROR",
                str(exc),
                details={
                    "stage": self.name,
                    "exception_type": type(
                        exc
                    ).__name__,
                },
            )


class ExecutionPipeline(Generic[T]):
    """
    Ordered execution pipeline.

    Each stage receives the previous stage's successful
    output. The pipeline stops immediately on failure.
    """

    def __init__(self) -> None:
        self._stages: list[
            PipelineStage[object, object]
        ] = []

    def add_stage(
        self,
        stage: PipelineStage[object, object],
    ) -> None:
        """Add a stage to the pipeline."""

        if not isinstance(stage.name, str) or not stage.name.strip():
            raise ValueError(
                "Pipeline stage name cannot be empty."
            )

        if any(
            existing.name == stage.name
            for existing in self._stages
        ):
            raise ValueError(
                f"Pipeline stage already exists: {stage.name}"
            )

        self._stages.append(stage)

    def stage_names(self) -> tuple[str, ...]:
        """Return the ordered stage names."""

        return tuple(
            stage.name
            for stage in self._stages
        )

    def stage_count(self) -> int:
        """Return the number of stages."""

        return len(self._stages)

    def execute(
        self,
        value: T,
    ) -> Result[object]:
        """Execute all stages in order."""

        current: object = value

        for stage in self._stages:
            result = stage.execute(current)

            if result.is_failure():
                return Result.fail(
                    result.error.code,
                    result.error.message,
                    details={
                        **result.error.details,
                        "failed_stage": stage.name,
                    },
                )

            current = result.data

        return Result.ok(current)

    def clear(self) -> None:
        """Remove all pipeline stages."""

        self._stages.clear()