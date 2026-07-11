from pathlib import Path

from core.completion_engine import CompletionEngine
from core.diagnostics import DiagnosticsEngine
from core.refactoring import RefactoringEngine
from core.workspace_watcher import WorkspaceWatcher


def test_diagnostics_detect_errors_and_warnings(tmp_path: Path):
    file_path = tmp_path / "sample.py"
    file_path.write_text("def broken(:\n    pass\n# TODO: remove me\n", encoding="utf-8")

    diagnostics = DiagnosticsEngine(tmp_path)
    issues = diagnostics.analyze(file_path)

    assert any(issue.kind == "error" for issue in issues)
    assert any(issue.kind == "warning" for issue in issues)


def test_completion_engine_suggests_keywords_and_symbols(tmp_path: Path):
    file_path = tmp_path / "sample.py"
    file_path.write_text("print\nmy_value = 1\n", encoding="utf-8")

    engine = CompletionEngine(tmp_path)
    suggestions = engine.complete(file_path, 1, 0)

    assert any(item.text == "print" for item in suggestions)


def test_refactoring_extract_method_and_rename_variable(tmp_path: Path):
    file_path = tmp_path / "sample.py"
    file_path.write_text("def demo():\n    value = 1\n    print(value)\n", encoding="utf-8")

    engine = RefactoringEngine(tmp_path)
    updated = engine.extract_method(file_path, 2, 4, "helper")
    assert "def helper()" in updated

    renamed = engine.rename_variable(file_path, "value", "amount")
    assert "amount" in renamed


def test_workspace_watcher_detects_changes(tmp_path: Path):
    watcher = WorkspaceWatcher(tmp_path)
    file_path = tmp_path / "watch.txt"
    file_path.write_text("one", encoding="utf-8")

    watcher.scan()
    file_path.write_text("two", encoding="utf-8")
    changed = watcher.scan()

    assert file_path.name in changed
