"""
GEETA AI IDE - Workspace Index
Version: 2.4.0

The workspace index is the in-process source of truth for parsed Python
artifacts, symbols, dependency information, and AI context.  Project metadata
is persisted by :class:`ProjectIndexer`; this class owns the coherent runtime
view built from that metadata.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Iterable

from core.context_builder import ContextBuilder, ProjectContext
from core.dependency_graph import DependencyGraph
from core.file_parser import FileParser, ParsedFile
from core.file_scanner import (
    IGNORED_DIRECTORIES,
    SUPPORTED_EXTENSIONS,
    FileInfo,
    FileScanner,
)
from core.project_indexer import ProjectIndexer
from core.symbol_table import Symbol, SymbolTable

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkspaceStatistics:
    """Statistics for the currently committed workspace index."""

    indexed_files: int = 0
    parsed_files: int = 0
    failed_files: int = 0
    symbols: int = 0
    dependencies: int = 0
    last_build_time: float = 0.0


@dataclass(frozen=True, slots=True)
class IndexFailure:
    """A non-fatal indexing failure associated with one workspace file."""

    path: str
    operation: str
    message: str


class WorkspaceIndex:
    """Coordinate project indexing and provide a consistent workspace view.

    ``WorkspaceIndex`` deliberately keeps all mutation behind one re-entrant
    lock.  Existing parsers and graph builders are stateful and SQLite writes
    performed by ``ProjectIndexer`` are synchronous, therefore serialising
    index mutations is required for correctness.  Query methods return copies
    so callers cannot mutate cached state after the lock is released.
    """

    _PARSABLE_EXTENSIONS = frozenset({".py"})

    def __init__(self, workspace: str | Path):
        self._lock = RLock()
        self.workspace = Path(workspace).expanduser().resolve()

        if not self.workspace.exists():
            raise FileNotFoundError(self.workspace)
        if not self.workspace.is_dir():
            raise NotADirectoryError(self.workspace)

        # Existing architectural components.  WorkspaceIndex coordinates them;
        # it does not duplicate their responsibilities.
        self.project_indexer = ProjectIndexer(self.workspace)
        self.scanner = FileScanner(self.workspace)
        self.parser = FileParser()
        self.symbol_table = SymbolTable()
        self.dependency_graph = DependencyGraph()
        self.context_builder = ContextBuilder(self.workspace)

        self.file_cache: dict[str, ParsedFile] = {}
        self.symbol_cache: dict[str, list[Symbol]] = {}
        self.context_cache: dict[str, ProjectContext] = {}
        self._indexed_paths: set[str] = set()
        self._failures: dict[str, IndexFailure] = {}
        self.statistics = WorkspaceStatistics()

        logger.info("WorkspaceIndex initialized for %s", self.workspace)

    @property
    def root(self) -> Path:
        """The resolved workspace root."""
        return self.workspace

    # ------------------------------------------------------------------
    # Full indexing
    # ------------------------------------------------------------------

    def build(self) -> int:
        """Build and atomically publish a complete workspace index.

        Metadata is first persisted through ``ProjectIndexer``.  Python source
        files are then parsed through the existing parser and symbol-table
        components.  Dependency and context caches are created from a fresh
        graph before the staged state replaces the previously committed state.

        Returns the number of supported files discovered in the workspace.
        """
        with self._lock:
            started = perf_counter()
            logger.info("Starting workspace build: %s", self.workspace)

            failures: dict[str, IndexFailure] = {}
            file_infos = self.scanner.scan()

            try:
                persisted_count = self.project_indexer.build_index()
            except Exception as exc:
                # Do not discard a previously usable runtime index if metadata
                # persistence fails before a new build can be committed.
                logger.exception("Project metadata indexing failed")
                self._record_failure(failures, self.workspace, "persist", exc)
                self._failures = failures
                self.statistics.failed_files = len(failures)
                self.statistics.last_build_time = perf_counter() - started
                raise

            parsed, symbols = self._stage_python_files(file_infos, failures)
            graph, builder = self._fresh_dependency_services()
            contexts = self._stage_contexts(parsed, builder, failures)

            self.file_cache = parsed
            self.symbol_cache = symbols
            self.context_cache = contexts
            self.dependency_graph = graph
            self.context_builder = builder
            self._indexed_paths = {
                self._key(info.path) for info in file_infos
            }
            self._failures = failures
            self._refresh_statistics(
                indexed_files=persisted_count,
                elapsed=perf_counter() - started,
            )

            logger.info(
                "Workspace build completed: %d files, %d parsed, %d failures",
                self.statistics.indexed_files,
                self.statistics.parsed_files,
                self.statistics.failed_files,
            )
            return self.statistics.indexed_files

    def rebuild(self) -> int:
        """Compatibility alias for :meth:`build`."""
        return self.build()

    def clear_cache(self) -> None:
        """Clear all runtime artifacts while retaining persisted metadata."""
        with self._lock:
            self.file_cache.clear()
            self.symbol_cache.clear()
            self.context_cache.clear()
            self._indexed_paths.clear()
            self._failures.clear()
            self.dependency_graph = DependencyGraph()
            self.context_builder = ContextBuilder(self.workspace)
            self._refresh_statistics(indexed_files=0, elapsed=0.0)
            logger.info("Workspace runtime cache cleared: %s", self.workspace)

    # ------------------------------------------------------------------
    # Incremental indexing
    # ------------------------------------------------------------------

    def index_file(self, file_path: str | Path) -> bool:
        """Index one existing workspace file without discarding valid state.

        A file is parsed and symbolised into local staging objects.  Only after
        both operations succeed are caches replaced.  Dependency and context
        information is rebuilt from the current workspace so changes in imports
        cannot leave AI context stale.
        """
        with self._lock:
            started = perf_counter()
            path = self._normalise_path(file_path)

            if path is None:
                return False
            if not path.exists() or not path.is_file():
                self._set_failure(path, "index", "File does not exist")
                return False
            if not self._is_indexable(path):
                self._set_failure(path, "index", "File is not indexable")
                return False

            key = self._key(path)
            staged_files = dict(self.file_cache)
            staged_symbols = {
                name: list(items) for name, items in self.symbol_cache.items()
            }
            failures = dict(self._failures)

            if path.suffix.lower() in self._PARSABLE_EXTENSIONS:
                try:
                    parsed, symbols = self._parse_and_symbolise(path)
                except Exception as exc:
                    logger.exception("Incremental indexing failed: %s", path)
                    self._record_failure(failures, path, "index", exc)
                    self._failures = failures
                    self.statistics.failed_files = len(failures)
                    return False

                staged_files[key] = parsed
                staged_symbols[key] = symbols
            else:
                # Non-Python supported files remain part of project metadata;
                # the existing parser stack intentionally has no parser for
                # them, so no artificial parsed representation is created.
                staged_files.pop(key, None)
                staged_symbols.pop(key, None)

            failures.pop(key, None)
            graph, builder = self._fresh_dependency_services()
            contexts = self._stage_contexts(staged_files, builder, failures)

            self.file_cache = staged_files
            self.symbol_cache = staged_symbols
            self.context_cache = contexts
            self.dependency_graph = graph
            self.context_builder = builder
            self._indexed_paths.add(key)
            self._failures = failures
            self._refresh_statistics(
                indexed_files=len(self._indexed_paths),
                elapsed=perf_counter() - started,
            )

            logger.info("Incremental indexing completed: %s", path)
            return True

    def refresh_file(self, file_path: str | Path) -> bool:
        """Refresh a file, retaining its previous artifacts if refresh fails."""
        return self.index_file(file_path)

    def index_files(self, files: Iterable[str | Path]) -> tuple[int, int]:
        """Index a batch of files and return ``(successful, failed)``."""
        successful = 0
        failed = 0
        for file_path in files:
            if self.index_file(file_path):
                successful += 1
            else:
                failed += 1
        logger.info("Batch indexing finished (%d success, %d failed)", successful, failed)
        return successful, failed

    def remove_file(self, file_path: str | Path) -> bool:
        """Remove a file from runtime state after it has been deleted or ignored."""
        with self._lock:
            started = perf_counter()
            path = self._normalise_path(file_path)
            if path is None:
                return False

            key = self._key(path)
            staged_files = dict(self.file_cache)
            staged_symbols = {
                name: list(items) for name, items in self.symbol_cache.items()
            }
            staged_files.pop(key, None)
            staged_symbols.pop(key, None)

            failures = dict(self._failures)
            failures.pop(key, None)
            graph, builder = self._fresh_dependency_services()
            contexts = self._stage_contexts(staged_files, builder, failures)

            self.file_cache = staged_files
            self.symbol_cache = staged_symbols
            self.context_cache = contexts
            self.dependency_graph = graph
            self.context_builder = builder
            self._indexed_paths.discard(key)
            self._failures = failures
            self._refresh_statistics(
                indexed_files=len(self._indexed_paths),
                elapsed=perf_counter() - started,
            )
            logger.info("Removed from workspace index: %s", path)
            return True

    # ------------------------------------------------------------------
    # Cache rebuilds
    # ------------------------------------------------------------------

    def rebuild_dependencies(self) -> None:
        """Rebuild the dependency graph and refresh context atomically."""
        with self._lock:
            started = perf_counter()
            failures = dict(self._failures)
            graph, builder = self._fresh_dependency_services()
            contexts = self._stage_contexts(self.file_cache, builder, failures)
            self.dependency_graph = graph
            self.context_builder = builder
            self.context_cache = contexts
            self._failures = failures
            self._refresh_statistics(
                indexed_files=len(self._indexed_paths),
                elapsed=perf_counter() - started,
            )

    def rebuild_context(self) -> None:
        """Recreate AI contexts from the current committed parsed file cache."""
        with self._lock:
            started = perf_counter()
            failures = dict(self._failures)
            graph, builder = self._fresh_dependency_services()
            contexts = self._stage_contexts(self.file_cache, builder, failures)
            self.dependency_graph = graph
            self.context_builder = builder
            self.context_cache = contexts
            self._failures = failures
            self._refresh_statistics(
                indexed_files=len(self._indexed_paths),
                elapsed=perf_counter() - started,
            )

    def rebuild_symbols(self) -> None:
        """Rebuild symbols from currently indexed Python files atomically."""
        with self._lock:
            started = perf_counter()
            failures = dict(self._failures)
            staged_symbols: dict[str, list[Symbol]] = {}

            for key in self.file_cache:
                path = self.workspace / key
                try:
                    staged_symbols[key] = self.symbol_table.parse(path)
                except Exception as exc:
                    logger.exception("Failed parsing symbols: %s", path)
                    self._record_failure(failures, path, "symbols", exc)

            self.symbol_cache = staged_symbols
            self._failures = failures
            self._refresh_statistics(
                indexed_files=len(self._indexed_paths),
                elapsed=perf_counter() - started,
            )

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get_file(self, file_path: str | Path) -> ParsedFile | None:
        with self._lock:
            key = self._key_from_input(file_path)
            value = self.file_cache.get(key) if key else None
            return deepcopy(value) if value is not None else None

    def get_symbols(self, file_path: str | Path) -> list[Symbol]:
        with self._lock:
            key = self._key_from_input(file_path)
            return deepcopy(self.symbol_cache.get(key, [])) if key else []

    def get_context(self, file_path: str | Path) -> ProjectContext | None:
        with self._lock:
            key = self._key_from_input(file_path)
            value = self.context_cache.get(key) if key else None
            return deepcopy(value) if value is not None else None

    def has_file(self, file_path: str | Path) -> bool:
        with self._lock:
            key = self._key_from_input(file_path)
            return key in self.file_cache if key else False

    def total_files(self) -> int:
        with self._lock:
            return len(self.file_cache)

    def total_symbols(self) -> int:
        with self._lock:
            return self.statistics.symbols

    def total_dependencies(self) -> int:
        with self._lock:
            return self.statistics.dependencies

    def failures(self) -> list[IndexFailure]:
        """Return failures in deterministic path order."""
        with self._lock:
            return [self._failures[key] for key in sorted(self._failures)]

    def cache_info(self) -> dict[str, int]:
        with self._lock:
            return {
                "files": len(self.file_cache),
                "symbols": len(self.symbol_cache),
                "contexts": len(self.context_cache),
            }

    def summary(self) -> dict[str, str | int | float]:
        with self._lock:
            return {
                "workspace": str(self.workspace),
                "indexed_files": self.statistics.indexed_files,
                "parsed_files": self.statistics.parsed_files,
                "failed_files": self.statistics.failed_files,
                "symbols": self.statistics.symbols,
                "dependencies": self.statistics.dependencies,
                "cache_size": len(self.file_cache),
                "build_time": self.statistics.last_build_time,
            }

    def workspace_info(self) -> dict[str, str | int | float]:
        with self._lock:
            return {
                "root": str(self.workspace),
                "indexed_files": self.statistics.indexed_files,
                "parsed_files": self.statistics.parsed_files,
                "failed_files": self.statistics.failed_files,
                "symbols": self.statistics.symbols,
                "dependencies": self.statistics.dependencies,
                "last_build_time": self.statistics.last_build_time,
            }

    def __len__(self) -> int:
        return self.total_files()

    def __contains__(self, file_path: object) -> bool:
        return isinstance(file_path, (str, Path)) and self.has_file(file_path)

    # ------------------------------------------------------------------
    # Internal implementation
    # ------------------------------------------------------------------

    def _stage_python_files(
        self,
        file_infos: Iterable[FileInfo],
        failures: dict[str, IndexFailure],
    ) -> tuple[dict[str, ParsedFile], dict[str, list[Symbol]]]:
        parsed_files: dict[str, ParsedFile] = {}
        symbols: dict[str, list[Symbol]] = {}

        for info in file_infos:
            if info.extension not in self._PARSABLE_EXTENSIONS:
                continue
            key = self._key(info.path)
            try:
                parsed, file_symbols = self._parse_and_symbolise(info.path)
            except Exception as exc:
                logger.exception("Failed processing %s", info.path)
                self._record_failure(failures, info.path, "parse", exc)
                continue
            parsed_files[key] = parsed
            symbols[key] = file_symbols

        return parsed_files, symbols

    def _parse_and_symbolise(self, path: Path) -> tuple[ParsedFile, list[Symbol]]:
        """Parse one Python file exactly once per supplied component call."""
        return self.parser.parse(path), self.symbol_table.parse(path)

    def _fresh_dependency_services(self) -> tuple[DependencyGraph, ContextBuilder]:
        graph = DependencyGraph()
        graph.build(self.workspace)
        # ContextBuilder currently owns its own DependencyGraph.  Creating it
        # after a graph rebuild keeps its internally used graph current.
        builder = ContextBuilder(self.workspace)
        return graph, builder

    def _stage_contexts(
        self,
        parsed_files: dict[str, ParsedFile],
        builder: ContextBuilder,
        failures: dict[str, IndexFailure],
    ) -> dict[str, ProjectContext]:
        contexts: dict[str, ProjectContext] = {}
        for key in parsed_files:
            path = self.workspace / key
            try:
                contexts[key] = builder.build(path)
            except Exception as exc:
                logger.exception("Failed building context: %s", path)
                self._record_failure(failures, path, "context", exc)
        return contexts

    def _refresh_statistics(self, *, indexed_files: int, elapsed: float) -> None:
        self.statistics.indexed_files = indexed_files
        self.statistics.parsed_files = len(self.file_cache)
        self.statistics.failed_files = len(self._failures)
        self.statistics.symbols = sum(len(items) for items in self.symbol_cache.values())
        self.statistics.dependencies = self.dependency_graph.total_dependencies()
        self.statistics.last_build_time = elapsed

    def _normalise_path(self, file_path: str | Path) -> Path | None:
        try:
            path = Path(file_path).expanduser()
            if not path.is_absolute():
                path = self.workspace / path
            path = path.resolve()
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            logger.warning("Invalid workspace path %r: %s", file_path, exc)
            return None
        if not self._is_within_workspace(path):
            logger.warning("Rejected path outside workspace: %s", path)
            return None
        return path

    def _key_from_input(self, file_path: str | Path) -> str | None:
        path = self._normalise_path(file_path)
        return self._key(path) if path is not None else None

    def _key(self, path: Path) -> str:
        return path.relative_to(self.workspace).as_posix()

    def _is_within_workspace(self, path: Path) -> bool:
        try:
            path.relative_to(self.workspace)
        except ValueError:
            return False
        return True

    def _is_indexable(self, path: Path) -> bool:
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False
        return not any(part in IGNORED_DIRECTORIES for part in path.relative_to(self.workspace).parts)

    def _set_failure(self, path: Path, operation: str, message: str) -> None:
        key = self._key(path)
        self._failures[key] = IndexFailure(key, operation, message)
        self.statistics.failed_files = len(self._failures)
        logger.warning("Workspace index %s failure for %s: %s", operation, path, message)

    def _record_failure(
        self,
        failures: dict[str, IndexFailure],
        path: Path,
        operation: str,
        exc: Exception,
    ) -> None:
        key = self._key(path) if self._is_within_workspace(path) else str(path)
        failures[key] = IndexFailure(key, operation, f"{type(exc).__name__}: {exc}")
