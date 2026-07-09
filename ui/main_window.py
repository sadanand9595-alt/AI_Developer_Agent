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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GEETA AI v1.0.0")
        self.resize(1300, 750)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # Left Panel
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("Project Explorer")
        self.project_tree.setMinimumWidth(280)

        root = QTreeWidgetItem(["GEETA_AI"])
        self.project_tree.addTopLevelItem(root)

        folders = [
            "agents",
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

        # Right Panel
        right = QVBoxLayout()

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Welcome to GEETA AI\n\nFuture AI coding will appear here..."
        )

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(180)
        self.console.setPlainText("Console Ready...")

        right.addWidget(QLabel("AI Workspace"))
        right.addWidget(self.editor)

        right.addWidget(QLabel("Console"))
        right.addWidget(self.console)

        layout.addWidget(self.project_tree)
        layout.addLayout(right)

        status = QStatusBar()
        status.showMessage("GEETA AI Loaded Successfully")
        self.setStatusBar(status)