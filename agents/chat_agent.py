from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.context_builder import ContextBuilder
from memory.agent_memory import AgentMemory


class ChatAgent:
    """Lightweight chat agent that returns context-aware responses using local project files."""

    def __init__(self, workspace: str | Path, memory: AgentMemory | None = None):
        self.workspace = Path(workspace).resolve()
        self.memory = memory or AgentMemory(self.workspace / "workspace_memory.json")
        self.context_builder = ContextBuilder(self.workspace)

    def build_context(self, prompt: str) -> str:
        return self.context_builder.build_context(prompt)

    def respond(self, prompt: str) -> str:
        context = self.build_context(prompt)
        history = self.memory.get("chat_history", [])
        if not isinstance(history, list):
            history = []
        history.append({"prompt": prompt, "response": context})
        self.memory.set("chat_history", history)
        return context

    def get_history(self) -> list[dict[str, Any]]:
        history = self.memory.get("chat_history", [])
        return history if isinstance(history, list) else []

    def clear_history(self) -> None:
        self.memory.delete("chat_history")
