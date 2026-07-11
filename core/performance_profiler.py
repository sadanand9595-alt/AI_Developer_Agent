from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class ProfileResult:
    duration_ms: float


class PerformanceProfiler:
    """Basic performance profiler for measuring operation runtime."""

    def measure(self, func: Callable[[], object]) -> ProfileResult:
        start = time.perf_counter()
        func()
        duration_ms = (time.perf_counter() - start) * 1000.0
        return ProfileResult(duration_ms=duration_ms)
