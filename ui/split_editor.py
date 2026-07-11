from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QTextEdit


class SplitEditor(QSplitter):
    """A functional split-view container with horizontal and vertical modes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.left_editor = QTextEdit(self)
        self.right_editor = QTextEdit(self)
        self.left_editor.setPlaceholderText("Left editor")
        self.right_editor.setPlaceholderText("Right editor")
        self.addWidget(self.left_editor)
        self.addWidget(self.right_editor)

    def set_vertical(self) -> None:
        self.setOrientation(Qt.Vertical)

    def set_horizontal(self) -> None:
        self.setOrientation(Qt.Horizontal)
