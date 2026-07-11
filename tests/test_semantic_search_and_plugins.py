from pathlib import Path

from core.plugin_system import PluginSystem
from core.semantic_search import SemanticSearch


def test_plugin_system_registers_and_lists_plugins(tmp_path: Path):
    plugins = PluginSystem()
    plugins.register("sample", lambda: "ok")

    assert plugins.list_plugins() == ["sample"]
    assert plugins.get("sample")() == "ok"


def test_semantic_search_finds_matches(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "alpha.py").write_text("print('hello world')\n", encoding="utf-8")

    search = SemanticSearch(workspace)
    assert search.search("world") == ["alpha.py"]
