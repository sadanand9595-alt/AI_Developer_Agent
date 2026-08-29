"""
Coordinator for execution context runtimes.

Provides a single application-facing boundary for creating,
accessing, operating, and removing execution runtimes.
"""

from __future__ import annotations

from core.execution_context_runtime import (
    ExecutionContextRuntime,
)
from core.execution_context_runtime_service import (
    ExecutionContextRuntimeService,
)
from core.execution_context_runtime_factory import (
    ExecutionContextRuntimeFactory,
)


class ExecutionContextRuntimeCoordinator:
    """Coordinates the lifecycle of execution runtimes."""

    def __init__(
        self,
        service: ExecutionContextRuntimeService | None = None,
    ) -> None:
        self._service = (
            service
            if service is not None
            else ExecutionContextRuntimeFactory.create()
        )

    def create(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Create and register a runtime."""

        return self._service.create(
            context_id
        )

    def register(
        self,
        runtime: ExecutionContextRuntime,
    ) -> None:
        """Register an existing runtime."""

        self._service.register(
            runtime
        )

    def get(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime | None:
        """Get a runtime by context ID."""

        return self._service.get(
            context_id
        )

    def contains(
        self,
        context_id: str,
    ) -> bool:
        """Return whether a runtime exists."""

        return self._service.contains(
            context_id
        )

    def start_step(
        self,
        context_id: str,
        step_name: str,
    ) -> ExecutionContextRuntime:
        """Start a step for a runtime."""

        runtime = self._require(
            context_id
        )

        runtime.start_step(
            step_name
        )

        return runtime

    def complete_step(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Complete the active step."""

        runtime = self._require(
            context_id
        )

        runtime.complete_step()

        return runtime

    def fail_step(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Fail the active step."""

        runtime = self._require(
            context_id
        )

        runtime.fail_step()

        return runtime

    def set_variable(
        self,
        context_id: str,
        name: str,
        value: object,
    ) -> ExecutionContextRuntime:
        """Set a runtime variable."""

        runtime = self._require(
            context_id
        )

        runtime.set_variable(
            name,
            value,
        )

        return runtime

    def get_variable(
        self,
        context_id: str,
        name: str,
        default: object = None,
    ) -> object:
        """Get a runtime variable."""

        runtime = self._require(
            context_id
        )

        return runtime.get_variable(
            name,
            default,
        )

    def remove_variable(
        self,
        context_id: str,
        name: str,
    ) -> bool:
        """Remove a runtime variable."""

        runtime = self._require(
            context_id
        )

        return runtime.remove_variable(
            name
        )

    def pause(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Pause a runtime."""

        runtime = self._require(
            context_id
        )

        runtime.pause()

        return runtime

    def resume(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Resume a runtime."""

        runtime = self._require(
            context_id
        )

        runtime.resume()

        return runtime

    def stop(
        self,
        context_id: str,
    ) -> bool:
        """Stop a runtime."""

        return self._service.stop(
            context_id
        )

    def unregister(
        self,
        context_id: str,
        *,
        stop: bool = True,
    ) -> bool:
        """Remove a runtime."""

        return self._service.unregister(
            context_id,
            stop=stop,
        )

    def count(self) -> int:
        """Return the number of active runtimes."""

        return self._service.count()

    def ids(self) -> tuple[str, ...]:
        """Return all runtime context IDs."""

        return self._service.ids()

    def all(
        self,
    ) -> tuple[ExecutionContextRuntime, ...]:
        """Return all registered runtimes."""

        return self._service.all()

    def snapshot(
        self,
        context_id: str,
    ) -> dict[str, object]:
        """Return a runtime snapshot."""

        runtime = self._require(
            context_id
        )

        return runtime.snapshot()

    def clear(
        self,
        *,
        stop: bool = True,
    ) -> int:
        """Clear all runtimes."""

        return self._service.clear(
            stop=stop
        )

    def _require(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Return runtime or raise KeyError."""

        runtime = self._service.get(
            context_id
        )

        if runtime is None:
            raise KeyError(
                f"Runtime not found: {context_id}"
            )

        return runtime


__all__ = [
    "ExecutionContextRuntimeCoordinator",
]