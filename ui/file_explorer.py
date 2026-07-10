from PySide6.QtWidgets import QTreeView, QFileSystemModel
from PySide6.QtCore import Signal


class FileExplorer(QTreeView):
    fileOpened = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = QFileSystemModel()
        self.model.setRootPath(".")

        self.setModel(self.model)
        self.setRootIndex(self.model.index("."))

        self.setAnimated(True)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.setHeaderHidden(False)
        self.setMinimumWidth(300)

        self.hideColumn(1)
        self.hideColumn(2)
        self.hideColumn(3)

        self.doubleClicked.connect(self.on_double_click)

    def open_project(self, folder_path):
        self.model.setRootPath(folder_path)
        self.setRootIndex(self.model.index(folder_path))

    def on_double_click(self, index):
        path = self.model.filePath(index)

        print("DOUBLE CLICK:", path)

        if self.model.isDir(index):
            return

        self.fileOpened.emit(path)