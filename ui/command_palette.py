from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QListWidget, QVBoxLayout


class CommandPaletteDialog(QDialog):
    """VS Code-style command palette for common IDE actions."""

    commandSelected = Signal(str)

    def __init__(self, parent=None):
        if QApplication.instance() is None:
            QApplication([])
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.resize(560, 320)

        layout = QVBoxLayout(self)
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Type a command")
        self.input.textChanged.connect(self.refresh_results)
        layout.addWidget(self.input)

        self.results = QListWidget(self)
        self.results.addItems(["Open File", "Save File", "Search Workspace", "Global Search", "Toggle Terminal", "New File", "Rename File"])
        self.results.itemDoubleClicked.connect(self._select_command)
        layout.addWidget(self.results)

    def refresh_results(self, text: str) -> None:
        query = text.strip().lower()
        self.results.clear()
        commands = ["Open File", "Save File", "Search Workspace", "Global Search", "Toggle Terminal", "New File", "Rename File"]
        for command in commands:
            if query in command.lower():
                self.results.addItem(command)

    def _select_command(self, item) -> None:
        self.commandSelected.emit(item.text())
        self.close()
