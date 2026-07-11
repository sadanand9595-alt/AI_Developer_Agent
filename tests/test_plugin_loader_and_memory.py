from pathlib import Path

from core.plugin_system import PluginSystem
from memory.agent_memory import AgentMemory


def test_plugin_system_auto_discovers_plugins(tmp_path: Path):
    plugins = PluginSystem(tmp_path)
    (tmp_path / "sample_plugin.py").write_text("from __future__ import annotations\n\nPLUGIN = lambda: 'ok'\n", encoding="utf-8")
    discovered = plugins.auto_discover()
    assert discovered == ["sample_plugin"]


def test_agent_memory_restores_values(tmp_path: Path):
    memory = AgentMemory(tmp_path / "memory.json")
    memory.set("workspace", "demo")
    restored = memory.restore("workspace")
    assert restored == "demo"
