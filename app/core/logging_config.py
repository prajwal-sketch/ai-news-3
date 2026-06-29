"""Structured logging configuration for the application."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from app.config.settings import settings


def configure_logging(log_dir: Optional[str] = None) -> None:
    """Configure rotating file handlers and named loggers for the platform."""
    log_path = Path(log_dir or "logs")
    log_path.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handlers: list[logging.Handler] = []
    for logger_name in ["application", "crawler", "pipeline", "database", "api"]:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / f"{logger_name}.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root_logger.handlers = []

    for handler in handlers:
        root_logger.addHandler(handler)

    for name in ["application", "crawler", "pipeline", "database", "api"]:
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        logger.propagate = False
        logger.handlers = []
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / f"{name}.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
