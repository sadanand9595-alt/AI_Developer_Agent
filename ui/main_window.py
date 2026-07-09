from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QLabel,
    QStatusBar,
)

from ui.menu_bar import MenuBarManager


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("GEETA AI v1.1.0")
        self.resize(1300, 750)

        # Create Menu Bar
        self.menu_manager = MenuBarManager(self)
        self.menu_manager.create()

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout()
        central.setLayout(layout)

        # Project Explorer
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("Project Explorer")
        self.project_tree.setMinimumWidth(280)

        root = QTreeWidgetItem(["GEETA_AI"])
        self.project_tree.addTopLevelItem(root)

        folders = [
            "agents",
            "config",
            "core",
            "database",
            "logs",
            "memory",
            "tools",
            "ui",
            "workspace",
        ]

        for folder in folders:
            root.addChild(QTreeWidgetItem([folder]))

        # Right Side
        right_layout = QVBoxLayout()

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Welcome to GEETA AI\n\nStart building your software..."
        )

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
        status.showMessage("GEETA AI v1.1.0 Ready")
        self.setStatusBar(status)