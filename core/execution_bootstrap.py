"""
Execution subsystem bootstrap for AI Command Center.

Provides controlled initialization and shutdown of the
top-level execution system.
"""

from __future__ import annotations

from threading import RLock

from core.execution_system import ExecutionSystem
from core.execution_system_factory import (
    ExecutionSystemFactory,
)


class ExecutionBootstrap:
    """Owns the application lifecycle of ExecutionSystem."""

    def __init__(self) -> None:
        self._system: ExecutionSystem | None = None
        self._lock = RLock()

    def initialize(self) -> ExecutionSystem:
        """
        Initialize and return the execution system.

        Initialization is idempotent: repeated calls return
        the same system instance.
        """

        with self._lock:
            if self._system is None:
                self._system = (
                    ExecutionSystemFactory.create()
                )

            return self._system

    def get(self) -> ExecutionSystem | None:
        """Return the initialized execution system."""

        with self._lock:
            return self._system

    def is_initialized(self) -> bool:
        """Return whether the execution system is initialized."""

        with self._lock:
            return self._system is not None

    def shutdown(self) -> None:
        """Shutdown the execution system."""

        with self._lock:
            if self._system is None:
                return

            self._system.close()
            self._system = None

    def restart(self) -> ExecutionSystem:
        """Shutdown the current system and initialize a new one."""

        with self._lock:
            if self._system is not None:
                self._system.close()

            # Clear the reference to the closed system before
            # attempting to build its replacement. If create()
            # raises, self._system must be None (an honest "not
            # initialized" state) rather than a stale reference
            # to a system that has already been closed.
            self._system = None

            self._system = (
                ExecutionSystemFactory.create()
            )

            return self._system


__all__ = [
    "ExecutionBootstrap",
]