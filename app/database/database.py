"""Database manager for SQLite persistence with SQLAlchemy."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage database initialization, sessions, and cleanup."""

    def __init__(self, database_url: str = "sqlite:///./ai_news.db") -> None:
        self._database_url = database_url
        self._engine = create_engine(database_url, connect_args={"check_same_thread": False})
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        self._initialized = False

    def initialize(self) -> None:
        """Create all tables when the database is first initialized."""
        try:
            Base.metadata.create_all(self._engine)
            self._initialized = True
            logger.info("tables created")
            logger.info("database connected")
        except SQLAlchemyError as exc:
            logger.exception("database connection failed", extra={"error": str(exc)})
            raise

    def get_session(self) -> Session:
        """Return a session bound to the database engine."""
        if not self._initialized:
            self.initialize()
        return self._session_factory()

    def close(self) -> None:
        """Close the database engine connections."""
        self._engine.dispose()
        logger.info("database closed")
