from pathlib import Path

from core.command_registry import CommandRegistry
from memory.agent_memory import AgentMemory
from ui.global_search import GlobalSearchDialog
from ui.quick_open import QuickOpenDialog


def test_command_registry_registers_and_runs_commands(tmp_path: Path):
    registry = CommandRegistry()
    executed = []

    registry.register("demo", lambda: executed.append("ok"))
    registry.run("demo")

    assert executed == ["ok"]


def test_agent_memory_persists_key_value_pairs(tmp_path: Path):
    memory = AgentMemory(tmp_path / "memory.json")
    memory.set("last_opened_file", "demo.py")

    reloaded = AgentMemory(tmp_path / "memory.json")
    assert reloaded.get("last_opened_file") == "demo.py"


def test_global_search_and_quick_open_dialogs_accept_workspace(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "sample.py").write_text("print('hello')\n", encoding="utf-8")

    quick_open = QuickOpenDialog(workspace)
    global_search = GlobalSearchDialog(workspace)

    assert quick_open.workspace == workspace.resolve()
    assert global_search.workspace == workspace.resolve()
