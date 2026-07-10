"""
==========================================================
GEETA AI IDE
Database Manager
Version : 2.3.0
==========================================================
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any


class DatabaseManager:
    """
    Central SQLite database manager for GEETA AI.

    Features
    --------
    - Singleton
    - Thread Safe
    - Auto Database Creation
    - Auto Schema Initialization
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:

        if hasattr(self, "_initialized"):
            return

        self._initialized = True

        self.project_root = Path(__file__).resolve().parent.parent

        self.database_dir = self.project_root / "database"

        self.database_path = self.database_dir / "project_index.db"

        self.schema_path = self.database_dir / "schema.sql"

        self.connection: sqlite3.Connection | None = None

        self.cursor: sqlite3.Cursor | None = None

        self._setup_logging()

        self.connect()

        self.initialize_database()

    # --------------------------------------------------

    def _setup_logging(self):

        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] %(message)s"
        )

    # --------------------------------------------------

    def connect(self):

        if self.connection is not None:
            return

        self.connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False
        )

        self.connection.row_factory = sqlite3.Row

        self.cursor = self.connection.cursor()

        logging.info("Database Connected")

    # --------------------------------------------------

    def initialize_database(self):

        if not self.schema_path.exists():

            raise FileNotFoundError(
                f"Schema file not found : {self.schema_path}"
            )

        with open(
            self.schema_path,
            "r",
            encoding="utf-8"
        ) as file:

            schema = file.read()

        self.connection.executescript(schema)

        self.connection.commit()

        logging.info("Database Initialized")

    # --------------------------------------------------

    def execute(
        self,
        query: str,
        parameters: tuple = ()
    ):

        self.cursor.execute(query, parameters)

        self.connection.commit()

        return self.cursor

    # --------------------------------------------------

    def executemany(
        self,
        query: str,
        parameters: list[tuple]
    ):

        self.cursor.executemany(query, parameters)

        self.connection.commit()

    # --------------------------------------------------

    def fetchone(
        self,
        query: str,
        parameters: tuple = ()
    ):

        self.cursor.execute(query, parameters)

        return self.cursor.fetchone()

    # --------------------------------------------------

    def fetchall(
        self,
        query: str,
        parameters: tuple = ()
    ):

        self.cursor.execute(query, parameters)

        return self.cursor.fetchall()

    # --------------------------------------------------

    def begin(self):

        self.connection.execute("BEGIN")

    # --------------------------------------------------

    def commit(self):

        self.connection.commit()

    # --------------------------------------------------

    def rollback(self):

        self.connection.rollback()

    # --------------------------------------------------

    def close(self):

        if self.connection:

            self.connection.close()

            self.connection = None

            self.cursor = None

            logging.info("Database Closed")


database = DatabaseManager()