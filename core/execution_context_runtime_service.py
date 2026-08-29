"""
Service for managing execution context runtimes.

Separates runtime lifecycle management from the mutable
ExecutionContextRuntime state object.
"""

from __future__ import annotations

from threading import RLock

from core.execution_context_runtime import (
    ExecutionContextRuntime,
)


class ExecutionContextRuntimeService:
    """Thread-safe service for execution runtimes."""

    def __init__(self) -> None:
        self._runtimes: dict[
            str,
            ExecutionContextRuntime,
        ] = {}
        self._lock = RLock()

    def create(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime:
        """Create and register a runtime."""

        normalized_id = context_id.strip()

        if not normalized_id:
            raise ValueError(
                "Context ID cannot be empty."
            )

        runtime = ExecutionContextRuntime(
            context_id=normalized_id
        )

        with self._lock:
            if normalized_id in self._runtimes:
                raise ValueError(
                    (
                        "Runtime already exists for context: "
                        f"{normalized_id}"
                    )
                )

            self._runtimes[
                normalized_id
            ] = runtime

        return runtime

    def register(
        self,
        runtime: ExecutionContextRuntime,
    ) -> None:
        """Register an existing runtime."""

        if not isinstance(
            runtime,
            ExecutionContextRuntime,
        ):
            raise TypeError(
                "Expected an ExecutionContextRuntime instance."
            )

        with self._lock:
            if runtime.context_id in self._runtimes:
                raise ValueError(
                    (
                        "Runtime already exists for context: "
                        f"{runtime.context_id}"
                    )
                )

            self._runtimes[
                runtime.context_id
            ] = runtime

    def get(
        self,
        context_id: str,
    ) -> ExecutionContextRuntime | None:
        """Return a runtime by context ID."""

        normalized_id = context_id.strip()

        if not normalized_id:
            return None

        with self._lock:
            return self._runtimes.get(
                normalized_id
            )

    def contains(
        self,
        context_id: str,
    ) -> bool:
        """Return whether a runtime exists."""

        return self.get(context_id) is not None

    def stop(
        self,
        context_id: str,
    ) -> bool:
        """Stop a runtime by context ID."""

        runtime = self.get(
            context_id
        )

        if runtime is None:
            return False

        runtime.stop()

        return True

    def unregister(
        self,
        context_id: str,
        *,
        stop: bool = True,
    ) -> bool:
        """Remove a runtime, optionally stopping it first."""

        normalized_id = context_id.strip()

        if not normalized_id:
            return False

        with self._lock:
            runtime = self._runtimes.get(
                normalized_id
            )

            if runtime is None:
                return False

            if stop:
                runtime.stop()

            del self._runtimes[
                normalized_id
            ]

            return True

    def count(self) -> int:
        """Return the number of registered runtimes."""

        with self._lock:
            return len(
                self._runtimes
            )

    def ids(self) -> tuple[str, ...]:
        """Return all registered context IDs."""

        with self._lock:
            return tuple(
                self._runtimes.keys()
            )

    def all(
        self,
    ) -> tuple[ExecutionContextRuntime, ...]:
        """Return all registered runtimes."""

        with self._lock:
            return tuple(
                self._runtimes.values()
            )

    def clear(
        self,
        *,
        stop: bool = True,
    ) -> int:
        """Remove all runtimes."""

        with self._lock:
            runtimes = tuple(
                self._runtimes.values()
            )

            if stop:
                for runtime in runtimes:
                    runtime.stop()

            count = len(
                runtimes
            )

            self._runtimes.clear()

            return count


__all__ = [
    "ExecutionContextRuntimeService",
]