from __future__ import annotations

from PySide6.QtWidgets import QToolTip


class HoverDocumentation:
    """Simple hover helper that shows documentation snippets for known symbols."""

    def __init__(self):
        self.docs = {
            "print": "Prints text to the console.",
            "def": "Defines a function.",
            "class": "Defines a class.",
        }

    def show(self, text: str, position):
        if text in self.docs:
            QToolTip.showText(position, self.docs[text])
