"""Structured logging configuration for the application."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from app.config.settings import settings


def configure_logging(log_dir: Optional[str] = None) -> None:
    """Configure logging for both console and rotating log files."""

    log_path = Path(log_dir or "logs")
    log_path.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (THIS IS WHAT WAS MISSING)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root_logger.handlers.clear()

    root_logger.addHandler(console_handler)

    logger_names = [
        "application",
        "pipeline",
        "crawler",
        "database",
        "api",
    ]

    for name in logger_names:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / f"{name}.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        logger.handlers.clear()

        # Only write to this logger's file
        logger.addHandler(file_handler)

        # Allow console output through the root logger
        logger.propagate = True
