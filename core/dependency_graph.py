"""
==========================================================
GEETA AI IDE
Dependency Graph
Version : 2.3.0
==========================================================

Builds a dependency graph for the workspace.

Uses:
    • FileParser
    • Imports
"""

from __future__ import annotations

from pathlib import Path
from collections import defaultdict

from core.file_parser import FileParser


class DependencyGraph:

    def __init__(self):

        self.parser = FileParser()

        self.graph: dict[str, set[str]] = defaultdict(set)

    # -----------------------------------------------------

    def build(self, workspace: str | Path):

        workspace = Path(workspace)

        self.graph.clear()

        for file in workspace.rglob("*.py"):

            try:

                parsed = self.parser.parse(file)

                current = str(file.relative_to(workspace))

                for imp in parsed.imports:

                    if imp.module:

                        self.graph[current].add(imp.module)

            except Exception:

                continue

        return self.graph

    # -----------------------------------------------------

    def dependencies_of(self, file: str):

        return sorted(self.graph.get(file, []))

    # -----------------------------------------------------

    def files(self):

        return sorted(self.graph.keys())

    # -----------------------------------------------------

    def total_dependencies(self):

        return sum(

            len(v)

            for v in self.graph.values()

        )

    # -----------------------------------------------------

    def print_graph(self):

        for file in sorted(self.graph):

            print()

            print(file)

            for dep in sorted(self.graph[file]):

                print(f"   └── {dep}")