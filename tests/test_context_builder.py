from core.context_builder import ContextBuilder
from pathlib import Path


def test_context_builder_creates_ai_context_from_actual_project_artifacts(workspace):
    context = ContextBuilder(workspace).build(workspace / "src" / "main.py")

    assert context.file_path == str(Path("src") / "main.py")
    assert context.language == "Python"
    assert context.imports == ["os", "src.helpers"]
    assert context.classes == ["Application"]
    assert context.functions == ["run", "shutdown"]
    assert context.dependencies == ["os", "src.helpers"]
