from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QFileDialog


class MenuBarManager:

    def __init__(self, window):
        self.window = window

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self.window,
            "Open Project Folder"
        )

        if folder:
            print("Selected Folder:", folder)
            self.window.project_tree.open_project(folder)

    def create(self):
        menu = self.window.menuBar()

        # File Menu
        file_menu = menu.addMenu("File")

        self.open_action = QAction("Open Folder", self.window)
        self.save_action = QAction("Save", self.window)
        self.exit_action = QAction("Exit", self.window)

        # Shortcuts
        self.save_action.setShortcut(QKeySequence.Save)
        self.open_action.setShortcut(QKeySequence.Open)

        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # Other Menus
        menu.addMenu("Edit")
        menu.addMenu("View")
        menu.addMenu("Tools")
        menu.addMenu("AI")
        menu.addMenu("Help")

        # Connections
        self.open_action.triggered.connect(self.open_folder)
        self.save_action.triggered.connect(self.window.save_file)
        self.exit_action.triggered.connect(self.window.close)