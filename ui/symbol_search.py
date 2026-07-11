from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLineEdit, QListWidget, QVBoxLayout

from core.symbol_table import SymbolTable


class SymbolSearchDialog(QDialog):
    def __init__(self, workspace, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self.table = SymbolTable()
        layout = QVBoxLayout(self)
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Search symbols")
        self.results = QListWidget(self)
        layout.addWidget(self.input)
        layout.addWidget(self.results)
        self.input.textChanged.connect(self.search)

    def search(self, query: str):
        self.results.clear()
        if not query:
            return
        for path in self.workspace.rglob("*.py"):
            try:
                symbols = self.table.parse(path)
            except Exception:
                continue
            for symbol in symbols:
                if query.lower() in symbol.name.lower():
                    self.results.addItem(f"{path.name}:{symbol.name}")
