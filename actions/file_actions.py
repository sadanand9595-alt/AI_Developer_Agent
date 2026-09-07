"""
Filesystem actions for AI Command Center.
"""

from __future__ import annotations

from pathlib import Path

from core.pipeline_context import PipelineContext
from core.result import Result


class FileActions:
    """Collection of controlled filesystem execution actions."""

    def write_file(
        self,
        context: PipelineContext,
    ) -> Result[object]:
        """Write file content described by the current execution step."""

        if not isinstance(context, PipelineContext):
            return Result.fail(
                "INVALID_PIPELINE_CONTEXT",
                "Expected a PipelineContext instance.",
            )

        current_step = context.get_metadata("current_step")

        if not isinstance(current_step, dict):
            return Result.fail(
                "MISSING_CURRENT_STEP",
                "Current execution step is missing from pipeline context.",
            )

        step_metadata = current_step.get("metadata")

        if not isinstance(step_metadata, dict):
            return Result.fail(
                "MISSING_STEP_METADATA",
                "Step metadata is missing or invalid.",
            )

        file_path = step_metadata.get("file_path")

        if not isinstance(file_path, str) or not file_path.strip():
            return Result.fail(
                "MISSING_FILE_PATH",
                "write_file requires a non-empty file_path.",
            )

        # -----------------------------------------------------
        # CONTENT RESOLUTION
        # -----------------------------------------------------
        #
        # Default behavior:
        #   Use explicit metadata["content"].
        #
        # Explicit pipeline handoff:
        #   If content_from_output=True, use the previous
        #   action's output stored in context.output_data.
        #
        # This prevents write_file from implicitly consuming
        # arbitrary pipeline output.
        # -----------------------------------------------------

        content = step_metadata.get("content")

        content_from_output = step_metadata.get(
            "content_from_output",
            False,
        )

        if content_from_output is True:
            content = context.output_data

        if not isinstance(content, str):
            return Result.fail(
                "INVALID_FILE_CONTENT",
                "write_file requires content as a string.",
            )

        normalized_path = Path(
            file_path
        ).expanduser()

        try:
            normalized_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            normalized_path.write_text(
                content,
                encoding="utf-8",
            )

        except OSError as exc:
            return Result.fail(
                "FILE_WRITE_ERROR",
                str(exc),
                details={
                    "file_path": str(normalized_path),
                    "exception_type": type(exc).__name__,
                },
            )

        return Result.ok(
            {
                "file_path": str(normalized_path),
                "bytes_written": len(
                    content.encode("utf-8")
                ),
                "status": "written",
            }
        )


__all__ = [
    "FileActions",
]
