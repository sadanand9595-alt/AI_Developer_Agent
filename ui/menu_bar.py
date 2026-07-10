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
        self.quick_open_action = QAction("Quick Open", self.window)
        self.search_action = QAction("Global Search", self.window)
        self.command_palette_action = QAction("Command Palette", self.window)
        self.exit_action = QAction("Exit", self.window)

        # Shortcuts
        self.save_action.setShortcut(QKeySequence.Save)
        self.open_action.setShortcut(QKeySequence.Open)
        self.quick_open_action.setShortcut(QKeySequence("Ctrl+P"))
        self.search_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.command_palette_action.setShortcut(QKeySequence("Ctrl+Shift+P"))

        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.quick_open_action)
        file_menu.addAction(self.search_action)
        file_menu.addAction(self.command_palette_action)
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
        self.quick_open_action.triggered.connect(lambda: self.window.quick_open_dialog.show())
        self.search_action.triggered.connect(lambda: self.window.global_search_dialog.show())
        self.command_palette_action.triggered.connect(lambda: self.window.command_palette_dialog.show())
        self.exit_action.triggered.connect(self.window.close)