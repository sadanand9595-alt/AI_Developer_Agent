from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QListWidget, QPushButton, QVBoxLayout, QWidget

from tools.git_tools import GitTools


class GitPanel(QDockWidget):
    """A dockable Git panel for showing repository status and actions."""

    def __init__(self, workspace, parent=None):
        super().__init__("Git", parent)
        self.workspace = workspace
        self.git = GitTools(workspace)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        self.status_list = QListWidget(self)
        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(self.status_list)
        layout.addWidget(self.refresh_button)
        self.setWidget(container)
        self.refresh()

    def refresh(self) -> None:
        self.status_list.clear()
        status = self.git.status()
        if status:
            for item in status.splitlines():
                self.status_list.addItem(item)
        else:
            self.status_list.addItem("Working tree clean")
