import os

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QTextEdit,
    QLabel,
    QStatusBar,
)

from ui.menu_bar import MenuBarManager
from ui.file_explorer import FileExplorer


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.current_file = None

        self.setWindowTitle("GEETA AI IDE v2.4.0")
        self.resize(1400, 800)

        # Menu
        self.menu_manager = MenuBarManager(self)
        self.menu_manager.create()

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout()
        central.setLayout(layout)

        # Left Panel
        self.project_tree = FileExplorer()
        self.project_tree.fileOpened.connect(self.open_file)

        # Right Panel
        right_layout = QVBoxLayout()

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Welcome to GEETA AI")

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(180)
        self.console.setPlainText("Console Ready...")

        right_layout.addWidget(QLabel("Editor"))
        right_layout.addWidget(self.editor)

        right_layout.addWidget(QLabel("Console"))
        right_layout.addWidget(self.console)

        layout.addWidget(self.project_tree)
        layout.addLayout(right_layout)

        status = QStatusBar()
        status.showMessage("GEETA AI IDE v2.4.0 Ready")
        self.setStatusBar(status)

    def open_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                text = file.read()

            self.current_file = file_path

            self.editor.setPlainText(text)

            self.setWindowTitle(
                f"GEETA AI - {os.path.basename(file_path)}"
            )

            self.statusBar().showMessage(file_path)

        except Exception as e:
            self.console.append(f"ERROR: {e}")

    def save_file(self):
        if self.current_file is None:
            self.console.append("No file is open.")
            return

        try:
            with open(self.current_file, "w", encoding="utf-8") as file:
                file.write(self.editor.toPlainText())

            self.statusBar().showMessage(
                f"Saved: {os.path.basename(self.current_file)}",
                3000
            )

            self.setWindowTitle(
                f"GEETA AI - {os.path.basename(self.current_file)}"
            )

        except Exception as e:
            self.console.append(f"ERROR: {e}")