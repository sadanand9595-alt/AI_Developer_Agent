from PySide6.QtGui import QAction


class MenuBarManager:

    def __init__(self, window):
        self.window = window

    def create(self):

        menu = self.window.menuBar()

        # File Menu
        file_menu = menu.addMenu("File")

        self.open_action = QAction("Open Folder", self.window)
        self.save_action = QAction("Save", self.window)
        self.exit_action = QAction("Exit", self.window)

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

        self.exit_action.triggered.connect(self.window.close)