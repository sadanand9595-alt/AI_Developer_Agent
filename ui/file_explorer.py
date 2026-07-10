from __future__ import annotations

from pathlib import Path
import shutil

from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QAction, QDrag, QIcon
from PySide6.QtWidgets import QTreeView, QFileSystemModel, QMenu, QMessageBox, QFileDialog


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

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeView.InternalMove)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.doubleClicked.connect(self.on_double_click)

    def open_project(self, folder_path):
        path = str(Path(folder_path).resolve())
        self.model.setRootPath(path)
        self.setRootIndex(self.model.index(path))

    def on_double_click(self, index):
        path = self.model.filePath(index)
        if self.model.isDir(index):
            return
        self.fileOpened.emit(path)

    def _show_context_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return
        path = Path(self.model.filePath(index))
        menu = QMenu(self)
        if path.is_dir():
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.fileOpened.emit(str(path)))
            menu.addAction(open_action)
        else:
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.fileOpened.emit(str(path)))
            menu.addAction(open_action)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename(path))
        menu.addAction(rename_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete(path))
        menu.addAction(delete_action)

        menu.addSeparator()
        new_file_action = QAction("New File", self)
        new_file_action.triggered.connect(lambda: self._create_file(path))
        menu.addAction(new_file_action)
        menu.exec_(self.viewport().mapToGlobal(position))

    def _rename(self, path: Path):
        if not path.exists():
            return
        new_name, ok = QFileDialog.getSaveFileName(self, "Rename", str(path))
        if ok and new_name:
            target = Path(new_name)
            if path.exists() and target != path:
                path.rename(target)
                self.open_project(str(path.parent))

    def _delete(self, path: Path):
        if not path.exists():
            return
        reply = QMessageBox.question(self, "Delete", f"Delete {path.name}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            self.open_project(str(path.parent))

    def _create_file(self, path: Path):
        target = path / "new_file.txt"
        if path.is_file():
            target = path.parent / "new_file.txt"
        target.touch(exist_ok=False)
        self.open_project(str(path if path.is_dir() else path.parent))

    def startDrag(self, supportedActions):
        index = self.currentIndex()
        if not index.isValid():
            return
        path = self.model.filePath(index)
        data = QMimeData()
        data.setText(path)
        drag = QDrag(self)
        drag.setMimeData(data)
        drag.exec_(Qt.CopyAction | Qt.MoveAction)
