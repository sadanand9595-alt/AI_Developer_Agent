"""
Logging configuration for AI Command Center.

Provides a consistent logging setup for the API, workers,
agents, tools, and background processes.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from config.settings import Settings


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(settings: Settings) -> None:
    """
    Configure application-wide logging.

    Logs are written to both stdout and a local log file.
    """

    log_level = getattr(
        logging,
        settings.log_level.upper(),
        None,
    )

    if not isinstance(log_level, int):
        raise ValueError(
            f"Invalid LOG_LEVEL: {settings.log_level!r}"
        )

    log_directory = Path("logs")
    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = log_directory / "application.log"

    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()

    root_logger.setLevel(log_level)

    root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named application logger.
    """

    return logging.getLogger(name)