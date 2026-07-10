from pathlib import Path
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QTextEdit,
    QLabel,
    QStatusBar,
)

from core.ai_code_review import AICodeReview
from core.ai_debugger import AIDebugger
from core.ai_refactor_engine import AIRefactorEngine
from core.code_actions import CodeActions
from core.command_registry import CommandRegistry
from core.completion_engine import CompletionEngine
from core.crash_reporter import CrashReporter
from core.debugger import Debugger
from core.language_server import LanguageServer
from core.language_support import LanguageSupport
from core.memory_analyzer import MemoryAnalyzer
from core.performance_profiler import PerformanceProfiler
from core.plugin_sdk import PluginSDK
from core.plugin_system import PluginSystem
from core.refactoring import RefactoringEngine
from core.semantic_search import SemanticSearch
from core.setting import SettingsManager
from core.update_system import UpdateSystem
from core.workspace_watcher import WorkspaceWatcher
from memory.agent_memory import AgentMemory
from ui.ai_chat_panel import AIChatPanel
from ui.command_palette import CommandPaletteDialog
from ui.file_explorer import FileExplorer
from ui.git_panel import GitPanel
from ui.global_search import GlobalSearchDialog
from ui.hover_doc import HoverDocumentation
from ui.menu_bar import MenuBarManager
from ui.problems_panel import ProblemsPanel
from ui.quick_open import QuickOpenDialog
from ui.symbol_search import SymbolSearchDialog


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.current_file = None
        self.memory = AgentMemory()
        self.workspace = self.memory.restore("workspace", os.getcwd())
        self.command_registry = CommandRegistry()
        self.plugin_system = PluginSystem()
        self.plugin_system.auto_discover()
        self.semantic_search = SemanticSearch(self.workspace)
        self.code_actions = CodeActions(self.workspace)
        self.completion_engine = CompletionEngine(self.workspace)
        self.refactoring_engine = RefactoringEngine(self.workspace)
        self.watcher = WorkspaceWatcher(self.workspace)
        self.settings = SettingsManager()
        self.language_server = LanguageServer(self.workspace)
        self.debugger = Debugger(self.workspace)
        self.plugin_sdk = PluginSDK(self.workspace)
        self.updater = UpdateSystem()
        self.ai_debugger = AIDebugger()
        self.ai_code_review = AICodeReview()
        self.ai_refactor_engine = AIRefactorEngine()
        self.language_support = LanguageSupport()
        self.performance_profiler = PerformanceProfiler()
        self.memory_analyzer = MemoryAnalyzer()
        self.crash_reporter = CrashReporter()

        self.setWindowTitle("GEETA AI IDE v2.4.1")
        self.resize(1400, 800)

        # Menu
        self.menu_manager = MenuBarManager(self)
        self.menu_manager.create()

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout()
        central.setLayout(layout)

        # Left Panel
        self.project_tree = FileExplorer()
        self.project_tree.fileOpened.connect(self.open_file)

        self.quick_open_dialog = QuickOpenDialog(self.workspace, self)
        self.quick_open_dialog.fileSelected.connect(self.open_file)

        self.global_search_dialog = GlobalSearchDialog(self.workspace, self)
        self.global_search_dialog.fileSelected.connect(self.open_file)

        self.command_palette_dialog = CommandPaletteDialog(self)
        self.command_palette_dialog.commandSelected.connect(self.handle_command)
        self.chat_panel = AIChatPanel(self.workspace, self)
        self.problems_panel = ProblemsPanel(self.workspace, self)
        self.git_panel = GitPanel(self.workspace, self)
        self.symbol_search_dialog = SymbolSearchDialog(Path(self.workspace), self)
        self.hover_doc = HoverDocumentation()
        self.addDockWidget(Qt.RightDockWidgetArea, self.chat_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.problems_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.git_panel)

        # Right Panel
        right_layout = QVBoxLayout()

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Welcome to GEETA AI")
        self.editor.textChanged.connect(self._on_editor_changed)
        self.editor.cursorPositionChanged.connect(self._on_cursor_moved)

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
        status.showMessage("GEETA AI IDE v2.4.1 Ready")
        self.setStatusBar(status)

        self._register_commands()

    def _register_commands(self):
        self.command_registry.register("Open File", lambda: self.quick_open_dialog.show())
        self.command_registry.register("Save File", self.save_file)
        self.command_registry.register("Search Workspace", lambda: self.global_search_dialog.show())
        self.command_registry.register("Global Search", lambda: self.global_search_dialog.show())
        self.command_registry.register("Toggle AI Chat", lambda: self.chat_panel.show())
        self.command_registry.register("Toggle Problems", lambda: self.problems_panel.show())
        self.command_registry.register("Toggle Git", lambda: self.git_panel.show())
        self.command_registry.register("Search Symbols", lambda: self.symbol_search_dialog.show())
        self.command_registry.register("Toggle Terminal", lambda: self.console.append("Integrated terminal ready."))
        self.command_registry.register("Open Settings", lambda: self.console.append(f"Theme: {self.settings.get('theme')}"))
        self.command_registry.register("Run Profiler", lambda: self.console.append("Profiler ready"))
        self.command_registry.register("Report Crash", lambda: self.console.append(self.crash_reporter.capture("Crash captured from IDE")))
        self.plugin_system.register("semantic_search", self.semantic_search.search)
        self.plugin_system.register("code_actions", self.code_actions.suggest)

    def handle_command(self, command_name: str):
        try:
            self.command_registry.run(command_name)
        except KeyError:
            self.console.append(f"Unknown command: {command_name}")

    def open_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                text = file.read()

            self.current_file = file_path

            self.editor.setPlainText(text)
            self.chat_panel.attach_current_file(file_path)
            self._refresh_problems(file_path)

            self.setWindowTitle(
                f"GEETA AI - {os.path.basename(file_path)}"
            )

            self.memory.set("last_opened_file", file_path)
            self.memory.set("workspace", self.workspace)
            self.console.append(f"Loaded {file_path}")
            self.statusBar().showMessage(file_path)

        except Exception as e:
            self.console.append(f"ERROR: {e}")

    def _on_editor_changed(self):
        if self.current_file:
            self._refresh_problems(self.current_file)
            self._refresh_watcher()
            self.chat_panel.attach_selected_code(self.editor.textCursor().selectedText())

    def _refresh_problems(self, file_path):
        self.problems_panel.refresh(file_path)

    def _on_cursor_moved(self):
        cursor = self.editor.textCursor()
        selected = cursor.selectedText().strip()
        if selected:
            self.hover_doc.show(selected, self.editor.mapToGlobal(cursor.rect().bottomLeft()))

    def _refresh_watcher(self):
        changed = self.watcher.scan()
        if changed:
            self.console.append(f"Workspace watcher refreshed: {', '.join(changed)}")

    def save_file(self):
        if self.current_file is None:
            self.console.append("No file is open.")
            return

        try:
            with open(self.current_file, "w", encoding="utf-8") as file:
                file.write(self.editor.toPlainText())

            self.statusBar().showMessage(
                f"Saved: {os.path.basename(self.current_file)}",
                3000
            )

            self.setWindowTitle(
                f"GEETA AI - {os.path.basename(self.current_file)}"
            )

        except Exception as e:
            self.console.append(f"ERROR: {e}")