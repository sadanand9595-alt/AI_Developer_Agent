from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from agents.chat_agent import ChatAgent


class AIChatPanel(QDockWidget):
    """A simple dockable chat panel that stores chat history and streams responses."""

    messageSent = Signal(str)

    def __init__(self, workspace: str | Path, parent=None):
        super().__init__("AI Chat", parent)
        self.workspace = Path(workspace).resolve()
        self.chat_agent = ChatAgent(self.workspace)

        container = QWidget(self)
        layout = QVBoxLayout(container)

        self.history = QListWidget(self)
        self.input_box = QTextEdit(self)
        self.current_file = None
        self.selected_code = ""
        self.input_box.setPlaceholderText("Ask GEETA AI about the workspace...")
        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_message)

        layout.addWidget(self.history)
        layout.addWidget(self.input_box)
        layout.addWidget(self.send_button)
        self.setWidget(container)

        self._refresh_history()

    def send_message(self) -> None:
        prompt = self.input_box.toPlainText().strip()
        if not prompt:
            return

        payload = prompt
        if self.current_file:
            payload += f"\n[Current file: {self.current_file}]"
        if self.selected_code:
            payload += f"\n[Selected code: {self.selected_code}]"

        response = self.chat_agent.respond(payload)
        self.messageSent.emit(prompt)
        self._refresh_history()
        self.input_box.clear()
        self.history.addItem(f"You: {prompt}")
        self.history.addItem(f"GEETA: {response}")

    def _refresh_history(self) -> None:
        self.history.clear()
        for entry in self.chat_agent.get_history():
            prompt = entry.get("prompt", "")
            response = entry.get("response", "")
            self.history.addItem(f"You: {prompt}")
            self.history.addItem(f"GEETA: {response}")

    def attach_current_file(self, file_path: str | None) -> None:
        self.current_file = file_path

    def attach_selected_code(self, code: str) -> None:
        self.selected_code = code

    def clear_history(self) -> None:
        self.chat_agent.clear_history()
        self._refresh_history()
