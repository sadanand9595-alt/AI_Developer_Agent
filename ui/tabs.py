from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtWidgets import QTabWidget, QTextEdit, QWidget


class EditorTabs(QTabWidget):
    """A functional multi-tab editor with close and pin support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._documents: Dict[str, QTextEdit] = {}
        self._pinned: set[str] = set()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.tabCloseRequested.connect(self.close_tab)

    def open_file(self, file_path: str | Path) -> None:
        path = str(Path(file_path))
        if path in self._documents:
            self.setCurrentWidget(self._documents[path])
            return

        editor = QTextEdit(self)
        editor.setPlaceholderText("Open a file to begin editing")
        self._documents[path] = editor
        self.addTab(editor, Path(path).name)
        self.setCurrentWidget(editor)

    def close_tab(self, index: int) -> None:
        widget = self.widget(index)
        if widget is None:
            return
        self.removeTab(index)
        for path, document in list(self._documents.items()):
            if document is widget:
                self._pinned.discard(path)
                del self._documents[path]
                break

    def pin_current_tab(self) -> None:
        current_path = self._path_for_widget(self.currentWidget())
        if current_path is None:
            return
        if current_path in self._pinned:
            self._pinned.remove(current_path)
        else:
            self._pinned.add(current_path)

    def _path_for_widget(self, widget: QWidget | None) -> str | None:
        for path, document in self._documents.items():
            if document is widget:
                return path
        return None
