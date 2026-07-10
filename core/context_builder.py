"""
==========================================================
GEETA AI IDE
Context Builder
Version : 2.3.0
==========================================================

Builds AI context for any project file.
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field

from core.file_parser import FileParser
from core.symbol_table import SymbolTable
from core.dependency_graph import DependencyGraph


@dataclass(slots=True)
class ProjectContext:
    file_path: str
    language: str
    imports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class ContextBuilder:

    def __init__(self, workspace: str | Path):

        self.workspace = Path(workspace)

        self.parser = FileParser()

        self.symbol_table = SymbolTable()

        self.graph = DependencyGraph()

        self.graph.build(self.workspace)

    # ------------------------------------------------------

    def build(self, file_path: str | Path) -> ProjectContext:

        file_path = Path(file_path)

        parsed = self.parser.parse(file_path)

        symbols = self.symbol_table.parse(file_path)

        context = ProjectContext(

            file_path=str(file_path.relative_to(self.workspace)),

            language=self._language(file_path.suffix)

        )

        # Imports

        context.imports = sorted(

            {

                item.module

                for item in parsed.imports

                if item.module

            }

        )

        # Classes

        context.classes = sorted(

            {

                symbol.name

                for symbol in symbols

                if symbol.symbol_type == "class"

            }

        )

        # Functions

        context.functions = sorted(

            {

                symbol.name

                for symbol in symbols

                if symbol.symbol_type in (

                    "function",

                    "method",

                    "async_function",

                    "async_method",

                )

            }

        )

        context.dependencies = self.graph.dependencies_of(

            context.file_path

        )

        return context

    # ------------------------------------------------------

    @staticmethod
    def _language(ext: str):

        mapping = {

            ".py": "Python",

            ".js": "JavaScript",

            ".ts": "TypeScript",

            ".tsx": "TypeScript",

            ".jsx": "JavaScript",

            ".json": "JSON",

            ".html": "HTML",

            ".css": "CSS",

            ".md": "Markdown",

        }

        return mapping.get(ext.lower(), "Unknown")