"""
AI provider abstraction for AI Command Center.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.result import Result


class AIProvider(ABC):
    """Abstract interface for AI model providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
    ) -> Result[str]:
        """Generate text from a prompt."""
        raise NotImplementedError
