"""
Agent runtime manager for AI Command Center.

Manages runtime instances for registered agents and provides
a controlled lookup boundary between persistent agent records
and in-memory execution runtimes.
"""

from __future__ import annotations

from threading import RLock

from core.agent_runtime import AgentRuntime
from core.result import Result


class AgentRuntimeManager:
    """Manage active AgentRuntime instances."""

    def __init__(self) -> None:
        self._runtimes: dict[str, AgentRuntime] = {}
        self._lock = RLock()

    def get_or_create(
        self,
        agent_id: str,
    ) -> Result[AgentRuntime]:
        """Return an existing runtime or create one."""

        normalized_id = agent_id.strip()

        if not normalized_id:
            return Result.fail(
                "INVALID_AGENT_ID",
                "Agent ID cannot be empty.",
            )

        with self._lock:
            runtime = self._runtimes.get(
                normalized_id
            )

            if runtime is None:
                runtime = AgentRuntime(
                    agent_id=normalized_id
                )

                self._runtimes[
                    normalized_id
                ] = runtime

            return Result.ok(runtime)

    def get(
        self,
        agent_id: str,
    ) -> Result[AgentRuntime]:
        """Return an existing runtime."""

        normalized_id = agent_id.strip()

        if not normalized_id:
            return Result.fail(
                "INVALID_AGENT_ID",
                "Agent ID cannot be empty.",
            )

        with self._lock:
            runtime = self._runtimes.get(
                normalized_id
            )

            if runtime is None:
                return Result.fail(
                    "RUNTIME_NOT_FOUND",
                    "Agent runtime was not found.",
                    details={
                        "agent_id": normalized_id,
                    },
                )

            return Result.ok(runtime)

    def remove(
        self,
        agent_id: str,
    ) -> Result[None]:
        """Remove an idle runtime from the manager."""

        normalized_id = agent_id.strip()

        if not normalized_id:
            return Result.fail(
                "INVALID_AGENT_ID",
                "Agent ID cannot be empty.",
            )

        with self._lock:
            runtime = self._runtimes.get(
                normalized_id
            )

            if runtime is None:
                return Result.fail(
                    "RUNTIME_NOT_FOUND",
                    "Agent runtime was not found.",
                    details={
                        "agent_id": normalized_id,
                    },
                )

            if runtime.status.value != "idle":
                return Result.fail(
                    "RUNTIME_BUSY",
                    "Cannot remove a non-idle agent runtime.",
                    details={
                        "agent_id": normalized_id,
                        "status": runtime.status.value,
                    },
                )

            del self._runtimes[
                normalized_id
            ]

            return Result.ok()

    def contains(
        self,
        agent_id: str,
    ) -> bool:
        """Return whether a runtime exists."""

        normalized_id = agent_id.strip()

        if not normalized_id:
            return False

        with self._lock:
            return normalized_id in self._runtimes

    def count(self) -> int:
        """Return the number of managed runtimes."""

        with self._lock:
            return len(self._runtimes)

    def clear_idle(self) -> int:
        """Remove all idle runtimes and return the count removed."""

        removed = 0

        with self._lock:
            idle_ids = [
                agent_id
                for agent_id, runtime
                in self._runtimes.items()
                if runtime.status.value == "idle"
            ]

            for agent_id in idle_ids:
                del self._runtimes[agent_id]
                removed += 1

        return removed