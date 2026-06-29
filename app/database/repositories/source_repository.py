"""Repository for source persistence operations."""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database.models import SourceORM
from app.models.source import Source

logger = logging.getLogger(__name__)


class SourceRepository:
    """Persist and query source records."""

    def __init__(self, session_factory: callable) -> None:
        self._session_factory = session_factory

    def save(self, source: Source) -> Source:
        """Persist a source and return it."""
        session = self._session_factory()
        try:
            orm_source = SourceORM(
                id=source.id,
                name=source.name,
                url=str(source.url),
                crawler=source.crawler.value,
                parser=source.parser.value,
                crawl_frequency=source.crawl_frequency,
                enabled=source.enabled,
                priority=source.priority,
                category=source.category.value,
                allowed_paths=source.allowed_paths,
                last_crawled=source.last_crawled,
            )
            session.add(orm_source)
            session.commit()
            logger.info("source saved")
            return source
        except IntegrityError as exc:
            session.rollback()
            logger.exception("constraint violation", extra={"error": str(exc)})
            raise
        except SQLAlchemyError as exc:
            session.rollback()
            logger.exception("database connection failed", extra={"error": str(exc)})
            raise
        finally:
            session.close()

    def save_source(self, source: Source) -> Source:
        """Backward-compatible alias for save."""
        return self.save(source)

    def get_source(self, source_id: str) -> Optional[Source]:
        """Return a source by its identifier."""
        session = self._session_factory()
        try:
            orm_source = session.get(SourceORM, source_id)
            if orm_source is None:
                return None
            return self._to_domain(orm_source)
        finally:
            session.close()

    def list_sources(self) -> List[Source]:
        """Return all sources."""
        session = self._session_factory()
        try:
            orm_sources = session.query(SourceORM).all()
            return [self._to_domain(item) for item in orm_sources]
        finally:
            session.close()

    def _to_domain(self, orm_source: SourceORM) -> Source:
        """Convert an ORM source to the domain model."""
        return Source(
            id=orm_source.id,
            name=orm_source.name,
            url=orm_source.url,
            crawler=orm_source.crawler,
            parser=orm_source.parser,
            crawl_frequency=orm_source.crawl_frequency,
            enabled=orm_source.enabled,
            priority=orm_source.priority,
            category=orm_source.category,
            allowed_paths=orm_source.allowed_paths or [],
            last_crawled=orm_source.last_crawled,
        )
