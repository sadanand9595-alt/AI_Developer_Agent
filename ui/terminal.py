from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QTextEdit, QTabWidget, QWidget


class IntegratedTerminal(QDockWidget):
    """A multi-terminal manager for IDE-like terminal workflows."""

    def __init__(self, parent=None):
        super().__init__("Terminal", parent)
        self.tabs = QTabWidget(self)
        self.output = None
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_terminal)
        self._terminals: list[QTextEdit] = []
        self.setWidget(self.tabs)
        self._initialize_output()

    def _initialize_output(self) -> None:
        terminal = self.new_terminal("Main")
        self.output = terminal

    def new_terminal(self, name: str = "Terminal") -> QTextEdit:
        terminal = QTextEdit(self)
        terminal.setReadOnly(True)
        terminal.setPlainText(f"Integrated terminal: {name}\n")
        self.output = terminal
        self.tabs.addTab(terminal, name)
        self._terminals.append(terminal)
        self.tabs.setCurrentWidget(terminal)
        return terminal

    def append_text(self, text: str) -> None:
        if not self._terminals:
            self.new_terminal()
        current = self.tabs.currentWidget()
        if isinstance(current, QTextEdit):
            current.append(text)

    def close_terminal(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if widget is None:
            return
        self.tabs.removeTab(index)
        if isinstance(widget, QTextEdit):
            self._terminals.remove(widget)
