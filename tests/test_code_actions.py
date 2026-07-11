from pathlib import Path

from core.code_actions import CodeActions


def test_code_actions_suggests_relevant_actions(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    sample = workspace / "sample.py"
    sample.write_text("import os\n\ndef hello():\n    return 'hi'\n", encoding="utf-8")

    actions = CodeActions(workspace)
    suggestions = actions.suggest(sample)

    assert "Extract function" in suggestions
    assert "Review imports" in suggestions
