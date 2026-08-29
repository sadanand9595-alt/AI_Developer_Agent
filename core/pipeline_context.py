"""
Pipeline execution context for AI Command Center.

Carries controlled data between execution pipeline stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from core.execution_context import ExecutionContext


@dataclass(slots=True)
class PipelineContext:
    """Mutable execution data shared between pipeline stages."""

    execution_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    task_id: str | None = None
    user_id: str | None = None
    agent_id: str | None = None

    execution_context: ExecutionContext | None = None

    input_data: object | None = None
    output_data: object | None = None

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    stage_results: dict[str, object] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def set_input(
        self,
        value: object,
    ) -> None:
        """Set the pipeline input."""

        self.input_data = value

    def set_output(
        self,
        value: object,
    ) -> None:
        """Set the pipeline output."""

        self.output_data = value

    def add_stage_result(
        self,
        stage_name: str,
        result: object,
    ) -> None:
        """Store the result produced by a pipeline stage."""

        normalized_name = stage_name.strip()

        if not normalized_name:
            raise ValueError(
                "Stage name cannot be empty."
            )

        self.stage_results[
            normalized_name
        ] = result

    def get_stage_result(
        self,
        stage_name: str,
    ) -> object | None:
        """Retrieve a stored stage result."""

        return self.stage_results.get(
            stage_name.strip()
        )

    def set_metadata(
        self,
        key: str,
        value: object,
    ) -> None:
        """Set pipeline metadata."""

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "Metadata key cannot be empty."
            )

        self.metadata[
            normalized_key
        ] = value

    def get_metadata(
        self,
        key: str,
        default: object | None = None,
    ) -> object | None:
        """Retrieve pipeline metadata."""

        return self.metadata.get(
            key.strip(),
            default,
        )

    def has_metadata(
        self,
        key: str,
    ) -> bool:
        """Return whether metadata exists."""

        return key.strip() in self.metadata

    def clear_stage_results(self) -> None:
        """Clear all stored stage results."""

        self.stage_results.clear()