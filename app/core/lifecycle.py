"""Lifecycle hooks for application startup and shutdown."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from app.core.exceptions import ConfigurationError, RegistryError
from app.database.database import DatabaseManager
from app.registry.source_registry import SourceRegistry

logger = logging.getLogger("application")


class ApplicationLifecycle:
    """Wraps startup and shutdown actions for the application container."""

    def __init__(self, database_manager: DatabaseManager, registry: SourceRegistry) -> None:
        self._database_manager = database_manager
        self._registry = registry

    def on_startup(self, app: FastAPI) -> None:
        """Initialize database resources and validate core dependencies."""
        logger.info("application startup initiated")
        try:
            self._database_manager.initialize()
            logger.info("database initialization complete", extra={"database_url": self._database_manager._database_url})
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise ConfigurationError(f"database initialization failed: {exc}") from exc

        try:
            self._registry.get_all_sources()
            logger.info("source registry loaded", extra={"source_count": len(self._registry.get_all_sources())})
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise RegistryError(f"registry validation failed: {exc}") from exc

        container = dict(getattr(app.state, "container", {}))
        container.update(
            {
                "database_manager": self._database_manager,
                "registry": self._registry,
            }
        )
        app.state.container = container
        logger.info("application startup complete", extra={"container_keys": sorted(container.keys())})

    def on_shutdown(self, app: FastAPI) -> None:
        """Release resources held by the application lifecycle."""
        self._database_manager.close()
        logger.info("application shutdown complete", extra={"database_url": self._database_manager._database_url})
