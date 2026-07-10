from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QListWidget, QVBoxLayout, QLabel

from core.file_scanner import FileScanner


class QuickOpenDialog(QDialog):
    """VS Code-like quick open dialog for navigation."""

    fileSelected = Signal(str)

    def __init__(self, workspace: str | Path, parent=None):
        if QApplication.instance() is None:
            QApplication([])
        super().__init__(parent)
        self.workspace = Path(workspace).resolve()
        self.scanner = FileScanner(self.workspace)

        self.setWindowTitle("Quick Open")
        self.resize(560, 380)

        layout = QVBoxLayout(self)
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Type a file name or path")
        self.input.textChanged.connect(self.refresh_results)
        layout.addWidget(self.input)

        self.status_label = QLabel("Start typing to filter files")
        layout.addWidget(self.status_label)

        self.results = QListWidget(self)
        self.results.itemDoubleClicked.connect(self._open_selection)
        layout.addWidget(self.results)

    def refresh_results(self, text: str) -> None:
        query = text.strip().lower()
        self.results.clear()
        if not query:
            self.status_label.setText("Start typing to filter files")
            return

        matches = []
        for info in self.scanner.scan():
            if query in info.relative_path.lower():
                matches.append(info.relative_path)
        self.results.addItems(matches)
        self.status_label.setText(f"{len(matches)} file(s) matched")

    def _open_selection(self, item) -> None:
        path = self.workspace / item.text()
        if path.exists():
            self.fileSelected.emit(str(path))
            self.close()
