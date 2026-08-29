"""
Application-level execution entry point for AI Command Center.

Provides a stable boundary between the application layer and
the internal execution bootstrap/system infrastructure.
"""

from __future__ import annotations

from core.execution_bootstrap import ExecutionBootstrap
from core.execution_manager import ExecutionRecord
from core.execution_tracker import ExecutionProgress
from core.execution_system import ExecutionSystem


class ExecutionApplication:
    """Application-facing owner of the execution subsystem."""

    def __init__(
        self,
        bootstrap: ExecutionBootstrap | None = None,
    ) -> None:
        self._bootstrap = (
            bootstrap
            if bootstrap is not None
            else ExecutionBootstrap()
        )

    def start(self) -> ExecutionSystem:
        """Initialize and return the execution system."""

        return self._bootstrap.initialize()

    def stop(self) -> None:
        """Shutdown the execution subsystem."""

        self._bootstrap.shutdown()

    def restart(self) -> ExecutionSystem:
        """Restart the execution subsystem."""

        return self._bootstrap.restart()

    def is_running(self) -> bool:
        """Return whether the execution subsystem is initialized."""

        return self._bootstrap.is_initialized()

    def system(self) -> ExecutionSystem:
        """
        Return the active execution system.

        Raises:
            RuntimeError: If the application has not been started.
        """

        system = self._bootstrap.get()

        if system is None:
            raise RuntimeError(
                "Execution application is not started."
            )

        return system

    def start_execution(
        self,
        execution_id: str,
        *,
        task_id: str | None = None,
        total_steps: int = 0,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Start an execution through the application boundary."""

        return self.system().start(
            execution_id,
            task_id=task_id,
            total_steps=total_steps,
            metadata=metadata,
        )

    def start_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Start an execution step."""

        return self.system().start_step(
            execution_id,
            step_name,
            task_id=task_id,
        )

    def complete_step(
        self,
        execution_id: str,
        step_name: str,
        *,
        task_id: str | None = None,
    ) -> ExecutionProgress:
        """Complete an execution step."""

        return self.system().complete_step(
            execution_id,
            step_name,
            task_id=task_id,
        )

    def complete(
        self,
        execution_id: str,
        *,
        output: object = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Complete an execution."""

        return self.system().complete(
            execution_id,
            output=output,
            metadata=metadata,
        )

    def fail(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        step_name: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Fail an execution."""

        return self.system().fail(
            execution_id,
            error_code=error_code,
            error_message=error_message,
            step_name=step_name,
            metadata=metadata,
        )

    def cancel(
        self,
        execution_id: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ExecutionRecord:
        """Cancel an execution."""

        return self.system().cancel(
            execution_id,
            metadata=metadata,
        )

    def get(
        self,
        execution_id: str,
    ) -> ExecutionRecord | None:
        """Get execution state."""

        return self.system().get(
            execution_id
        )

    def get_progress(
        self,
        execution_id: str,
    ) -> ExecutionProgress | None:
        """Get execution progress."""

        return self.system().get_progress(
            execution_id
        )

    def get_observation(
        self,
        execution_id: str,
    ):
        """Get execution observation."""

        return self.system().get_observation(
            execution_id
        )

    def get_audit(
        self,
        execution_id: str,
    ):
        """Get execution audit records."""

        return self.system().get_audit(
            execution_id
        )

    def active_count(self) -> int:
        """Return active execution count."""

        return self.system().active_count()

    def registered_count(self) -> int:
        """Return registered execution count."""

        return self.system().registered_count()

    def audit_count(self) -> int:
        """Return audit record count."""

        return self.system().audit_count()


__all__ = [
    "ExecutionApplication",
]