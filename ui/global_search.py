from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QListWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QHBoxLayout

from core.file_scanner import FileScanner


class GlobalSearchDialog(QDialog):
    """A real global search dialog with live filtering and replace support."""

    fileSelected = Signal(str)

    def __init__(self, workspace: str | Path, parent=None):
        if QApplication.instance() is None:
            QApplication([])
        super().__init__(parent)
        self.workspace = Path(workspace).resolve()
        self.scanner = FileScanner(self.workspace)

        self.setWindowTitle("Global Search")
        self.resize(760, 500)

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search text")
        self.search_input.textChanged.connect(self.refresh_results)
        top.addWidget(self.search_input)

        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText("Replace with")
        top.addWidget(self.replace_input)
        layout.addLayout(top)

        self.results = QListWidget(self)
        self.results.itemDoubleClicked.connect(self._open_selection)
        layout.addWidget(self.results)

        self.status_label = QLabel("Type a query to search files")
        layout.addWidget(self.status_label)

        actions = QHBoxLayout()
        self.replace_button = QPushButton("Replace", self)
        self.replace_button.clicked.connect(self.replace_matches)
        actions.addWidget(self.replace_button)
        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.close)
        actions.addWidget(self.close_button)
        layout.addLayout(actions)

    def refresh_results(self, text: str) -> None:
        query = text.strip().lower()
        self.results.clear()
        if not query:
            self.status_label.setText("Type a query to search files")
            return

        matches = []
        for info in self.scanner.scan():
            path = self.workspace / info.relative_path
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if query in content.lower():
                matches.append(info.relative_path)
        self.results.addItems(matches)
        self.status_label.setText(f"{len(matches)} file(s) matched")

    def replace_matches(self) -> None:
        query = self.search_input.text().strip()
        replacement = self.replace_input.text()
        if not query:
            return
        for index in range(self.results.count()):
            relative_path = self.results.item(index).text()
            path = self.workspace / relative_path
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            updated = text.replace(query, replacement)
            if updated != text:
                path.write_text(updated, encoding="utf-8")
        self.refresh_results(query)

    def _open_selection(self, item) -> None:
        path = self.workspace / item.text()
        if path.exists():
            self.fileSelected.emit(str(path))
            self.close()
