from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QListWidget, QWidget, QVBoxLayout

from core.diagnostics import DiagnosticsEngine


class ProblemsPanel(QDockWidget):
    def __init__(self, workspace, parent=None):
        super().__init__("Problems", parent)
        self.workspace = workspace
        self.engine = DiagnosticsEngine(workspace)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        self.list = QListWidget(self)
        layout.addWidget(self.list)
        self.setWidget(container)

    def refresh(self, file_path=None):
        self.list.clear()
        if file_path is None:
            return
        for issue in self.engine.analyze(file_path):
            self.list.addItem(f"{issue.kind.upper()} {issue.line}: {issue.message}")
