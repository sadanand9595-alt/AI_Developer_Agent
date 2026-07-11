from pathlib import Path

from core.debugger import Debugger
from core.language_server import LanguageServer
from core.plugin_sdk import PluginSDK
from core.setting import SettingsManager
from core.update_system import UpdateSystem
from tools.git_tools import GitTools


def test_settings_manager_persists_defaults(tmp_path: Path):
    settings = SettingsManager(tmp_path / "settings.json")
    assert settings.get("theme") == "dark"
    settings.set("font_size", 14)
    assert settings.get("font_size") == 14


def test_language_server_reports_capabilities():
    server = LanguageServer(".")
    assert server.capabilities()["completion"] is True


def test_debugger_tracks_breakpoints_and_call_stack(tmp_path: Path):
    debugger = Debugger(tmp_path)
    debugger.toggle_breakpoint(tmp_path / "app.py", 4)
    assert debugger.get_call_stack() == []
    debugger.step_into()
    assert debugger.get_call_stack()


def test_plugin_sdk_registers_handlers():
    sdk = PluginSDK(".")
    sdk.register("demo", lambda: None)
    assert "demo" in sdk.list_plugins()


def test_update_checker_returns_optional_value():
    checker = UpdateSystem("3.0.0")
    assert checker.current_version == "3.0.0"


def test_git_panel_helper_still_works(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "file.txt").write_text("hello", encoding="utf-8")
    tools = GitTools(repo)
    assert tools.status() != ""
