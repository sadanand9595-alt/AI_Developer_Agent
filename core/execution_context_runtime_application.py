"""
Application-facing API for execution context runtimes.

Keeps runtime lifecycle and operations behind a stable
application boundary.
"""

from __future__ import annotations

from core.execution_context_runtime import (
    ExecutionContextRuntime,
)
from core.execution_context_runtime_coordinator import (
    ExecutionContextRuntimeCoordinator,
)
from core.execution_context_runtime_coordinator_factory import (
    ExecutionContextRuntimeCoordinatorFactory,
)


class ExecutionContextRuntimeApplication:
    """Application-facing owner of execution runtimes."""

    def __init__(
        self,
        coordinator: (
            ExecutionContextRuntimeCoordinator | None
        ) = None,
    ) -> None:
        self._coordinator = (
            coordinator
            if coordinator is not None
            else (
                ExecutionContextRuntimeCoordinatorFactory.create()
            )
        )

    def create(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Create and register a runtime."""

        return self._coordinator.create(
            context_id
        )

    def register(
        self,
        runtime: ExecutionContextRuntime,
    ) -> None:
        """Register an existing runtime."""

        self._coordinator.register(
            runtime
        )

    def get(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime | None:
        """Get a runtime by context ID."""

        return self._coordinator.get(
            context_id
        )

    def contains(
        self,
        context_id: str,
    ) -> bool:
        """Return whether a runtime exists."""

        return self._coordinator.contains(
            context_id
        )

    def start_step(
        self,
        context_id: str,
        step_name: str,
    ) -> ExecutionContextRuntime:
        """Start a runtime step."""

        return self._coordinator.start_step(
            context_id,
            step_name,
        )

    def complete_step(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Complete the active runtime step."""

        return self._coordinator.complete_step(
            context_id
        )

    def fail_step(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Fail the active runtime step."""

        return self._coordinator.fail_step(
            context_id
        )

    def set_variable(
        self,
        context_id: str,
        name: str,
        value: object,
    ) -> ExecutionContextRuntime:
        """Set a runtime variable."""

        return self._coordinator.set_variable(
            context_id,
            name,
            value,
        )

    def get_variable(
        self,
        context_id: str,
        name: str,
        default: object = None,
    ) -> object:
        """Get a runtime variable."""

        return self._coordinator.get_variable(
            context_id,
            name,
            default,
        )

    def remove_variable(
        self,
        context_id: str,
        name: str,
    ) -> bool:
        """Remove a runtime variable."""

        return self._coordinator.remove_variable(
            context_id,
            name,
        )

    def pause(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Pause a runtime."""

        return self._coordinator.pause(
            context_id
        )

    def resume(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Resume a runtime."""

        return self._coordinator.resume(
            context_id
        )

    def stop(
        self,
        context_id: str,
    ) -> bool:
        """Stop a runtime."""

        return self._coordinator.stop(
            context_id
        )

    def unregister(
        self,
        context_id: str,
        *,
        stop: bool = True,
    ) -> bool:
        """Remove a runtime."""

        return self._coordinator.unregister(
            context_id,
            stop=stop,
        )

    def snapshot(
        self,
        context_id: str,
    ) -> dict[str, object]:
        """Return a runtime snapshot."""

        return self._coordinator.snapshot(
            context_id
        )

    def count(self) -> int:
        """Return the number of active runtimes."""

        return self._coordinator.count()

    def ids(self) -> tuple[str, ...]:
        """Return all runtime context IDs."""

        return self._coordinator.ids()

    def all(
        self,
    ) -> tuple[ExecutionContextRuntime, ...]:
        """Return all registered runtimes."""

        return self._coordinator.all()

    def clear(
        self,
        *,
        stop: bool = True,
    ) -> int:
        """Clear all runtimes."""

        return self._coordinator.clear(
            stop=stop
        )


__all__ = [
    "ExecutionContextRuntimeApplication",
]