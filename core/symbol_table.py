"""
==========================================================
GEETA AI IDE
Symbol Table
Version : 2.3.0
==========================================================

Builds a symbol table from Python source files.

Extracts:
    • Classes
    • Methods
    • Functions
    • Async Functions

Uses ast.NodeVisitor for accurate symbol hierarchy.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------
# Symbol Model
# ---------------------------------------------------------

@dataclass(slots=True)
class Symbol:

    name: str

    symbol_type: str

    line: int

    parent: str | None = None

    arguments: list[str] = field(default_factory=list)

    docstring: str = ""


# ---------------------------------------------------------
# Visitor
# ---------------------------------------------------------

class SymbolVisitor(ast.NodeVisitor):

    def __init__(self):

        self.symbols: list[Symbol] = []

        self.current_class: str | None = None

    # -----------------------------------------------------

    def visit_ClassDef(self, node: ast.ClassDef):

        self.symbols.append(

            Symbol(

                name=node.name,

                symbol_type="class",

                line=node.lineno,

                docstring=ast.get_docstring(node) or "",

            )

        )

        previous = self.current_class

        self.current_class = node.name

        self.generic_visit(node)

        self.current_class = previous

    # -----------------------------------------------------

    def visit_FunctionDef(self, node: ast.FunctionDef):

        args = [arg.arg for arg in node.args.args]

        self.symbols.append(

            Symbol(

                name=node.name,

                symbol_type="method" if self.current_class else "function",

                line=node.lineno,

                parent=self.current_class,

                arguments=args,

                docstring=ast.get_docstring(node) or "",

            )

        )

        self.generic_visit(node)

    # -----------------------------------------------------

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):

        args = [arg.arg for arg in node.args.args]

        self.symbols.append(

            Symbol(

                name=node.name,

                symbol_type="async_method" if self.current_class else "async_function",

                line=node.lineno,

                parent=self.current_class,

                arguments=args,

                docstring=ast.get_docstring(node) or "",

            )

        )

        self.generic_visit(node)


# ---------------------------------------------------------
# Symbol Table
# ---------------------------------------------------------

class SymbolTable:

    def parse(self, file_path: str | Path) -> list[Symbol]:

        file_path = Path(file_path)

        source = file_path.read_text(

            encoding="utf-8",

            errors="ignore"

        )

        tree = ast.parse(source)

        visitor = SymbolVisitor()

        visitor.visit(tree)

        return visitor.symbols