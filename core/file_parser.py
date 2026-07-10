"""
==========================================================
GEETA AI IDE
File Parser
Version : 2.3.0
==========================================================

Parses Python source files using the AST module.

Extracts:
    • Imports
    • Classes
    • Functions
    • Docstrings
"""

from __future__ import annotations

import ast
from pathlib import Path
from dataclasses import dataclass, field


# ---------------------------------------------------------
# Data Models
# ---------------------------------------------------------

@dataclass(slots=True)
class ImportInfo:
    module: str
    name: str = ""
    alias: str = ""


@dataclass(slots=True)
class FunctionInfo:
    name: str
    line: int
    class_name: str | None = None
    arguments: list[str] = field(default_factory=list)
    docstring: str = ""


@dataclass(slots=True)
class ClassInfo:
    name: str
    line: int
    docstring: str = ""


@dataclass(slots=True)
class ParsedFile:

    path: Path

    imports: list[ImportInfo] = field(default_factory=list)

    classes: list[ClassInfo] = field(default_factory=list)

    functions: list[FunctionInfo] = field(default_factory=list)


# ---------------------------------------------------------
# Parser
# ---------------------------------------------------------

class FileParser:

    def parse(self, file_path: str | Path) -> ParsedFile:

        file_path = Path(file_path)

        source = file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        tree = ast.parse(source)

        parsed = ParsedFile(path=file_path)

        self._visit(tree, parsed)

        return parsed

    # -----------------------------------------------------

    def _visit(self, tree, parsed):

        for node in ast.walk(tree):

            # -----------------------------
            # Imports
            # -----------------------------

            if isinstance(node, ast.Import):

                for alias in node.names:

                    parsed.imports.append(

                        ImportInfo(

                            module=alias.name,

                            alias=alias.asname or ""

                        )

                    )

            elif isinstance(node, ast.ImportFrom):

                module = node.module or ""

                for alias in node.names:

                    parsed.imports.append(

                        ImportInfo(

                            module=module,

                            name=alias.name,

                            alias=alias.asname or ""

                        )

                    )

            # -----------------------------
            # Classes
            # -----------------------------

            elif isinstance(node, ast.ClassDef):

                parsed.classes.append(

                    ClassInfo(

                        name=node.name,

                        line=node.lineno,

                        docstring=ast.get_docstring(node) or ""

                    )

                )

            # -----------------------------
            # Functions
            # -----------------------------

            elif isinstance(node, ast.FunctionDef):

                arguments = [

                    arg.arg

                    for arg in node.args.args

                ]

                parsed.functions.append(

                    FunctionInfo(

                        name=node.name,

                        line=node.lineno,

                        arguments=arguments,

                        docstring=ast.get_docstring(node) or ""

                    )

                )