"""Repository for crawl log persistence operations."""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database.models import CrawlLogORM
from app.models.crawl_job import CrawlJob

logger = logging.getLogger(__name__)


class CrawlRepository:
    """Persist and query crawl logs."""

    def __init__(self, session_factory: callable) -> None:
        self._session_factory = session_factory

    def save(self, crawl_job: CrawlJob, status: str, details: Optional[str] = None) -> None:
        """Save a crawl log entry."""
        session = self._session_factory()
        try:
            orm_log = CrawlLogORM(
                job_id=str(crawl_job.source.id),
                source_id=str(crawl_job.source.id),
                status=status,
                details=details,
            )
            session.add(orm_log)
            session.commit()
            logger.info("crawl log saved")
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

    def save_log(self, crawl_job: CrawlJob, status: str, details: Optional[str] = None) -> None:
        """Backward-compatible alias for save."""
        self.save(crawl_job, status, details)

    def get_logs(self, job_id: Optional[UUID | str] = None) -> List[CrawlLogORM]:
        """Return crawl logs, optionally filtered by job id."""
        session = self._session_factory()
        try:
            query = session.query(CrawlLogORM)
            if job_id is not None:
                query = query.filter(CrawlLogORM.job_id == str(job_id))
            return query.order_by(CrawlLogORM.timestamp.desc()).all()
        finally:
            session.close()
