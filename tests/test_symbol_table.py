from core.symbol_table import SymbolTable


def test_symbol_table_preserves_class_and_async_function_structure(workspace):
    symbols = SymbolTable().parse(workspace / "src" / "main.py")

    assert [(symbol.name, symbol.symbol_type, symbol.parent) for symbol in symbols] == [
        ("Application", "class", None),
        ("run", "method", "Application"),
        ("shutdown", "async_function", None),
    ]
    assert symbols[1].arguments == ["self", "value"]
    assert symbols[0].docstring == "Application entry point."
