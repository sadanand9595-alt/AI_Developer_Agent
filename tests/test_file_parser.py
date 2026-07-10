from core.file_parser import FileParser


def test_parse_extracts_imports_classes_and_functions(workspace):
    parsed = FileParser().parse(workspace / "src" / "main.py")

    assert [(item.module, item.name) for item in parsed.imports] == [
        ("os", ""),
        ("src.helpers", "greeting"),
    ]
    assert [(item.name, item.line) for item in parsed.classes] == [("Application", 5)]
    assert [(item.name, item.line) for item in parsed.functions] == [("run", 8)]
    assert parsed.functions[0].arguments == ["self", "value"]


def test_parse_raises_syntax_error_for_invalid_python(workspace):
    invalid = workspace / "invalid.py"
    invalid.write_text("def broken(:\n", encoding="utf-8")

    try:
        FileParser().parse(invalid)
    except SyntaxError:
        pass
    else:
        raise AssertionError("FileParser must report invalid Python syntax")
