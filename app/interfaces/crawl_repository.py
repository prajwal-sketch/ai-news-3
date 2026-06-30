"""Repository interface for crawl logging."""

from __future__ import annotations

from typing import List, Optional, Protocol
from uuid import UUID

from app.database.models import CrawlLogORM


class CrawlRepository(Protocol):
    """Interface for persisting and querying crawl logs."""

    def save(self, crawl_job: object, status: str, details: Optional[str] = None) -> None:
        """Persist a crawl log entry."""

    def get_logs(self, job_id: Optional[UUID | str] = None) -> List[CrawlLogORM]:
        """Return crawl logs for the optional job identifier."""
