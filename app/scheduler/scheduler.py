"""Scheduler for selecting which sources should be crawled next."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List

from app.models.crawl_job import CrawlJob
from app.registry.source_registry import Source, SourceRegistry

logger = logging.getLogger(__name__)


class Scheduler:
    """Selects due crawl jobs from the enabled source registry.

    The scheduler is responsible only for deciding which sources should be
    crawled next. It never performs crawling itself.
    """

    _FREQUENCY_MAP: dict[str, timedelta] = {
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "6h": timedelta(hours=6),
        "12h": timedelta(hours=12),
        "24h": timedelta(hours=24),
    }

    def __init__(self, registry: SourceRegistry) -> None:
        self.registry = registry

    def get_due_jobs(self, max_jobs: int = 3) -> List[CrawlJob]:
        """Return up to ``max_jobs`` due crawl jobs sorted by priority."""
        now = self._get_now()
        logger.info("scheduler started", extra={"now": now.isoformat(), "max_jobs": max_jobs})

        enabled_sources = self.registry.get_enabled_sources()
        logger.debug(
            "enabled sources loaded",
            extra={"source_count": len(enabled_sources)},
        )

        due_jobs: List[CrawlJob] = []
        skipped_sources: List[str] = []
        due_sources: List[str] = []

        for source in enabled_sources:
            if not self._is_due(source, now):
                skipped_sources.append(source.name)
                continue

            due_sources.append(source.name)
            due_jobs.append(self._build_job(source, now))

        due_jobs.sort(key=lambda job: (job.priority, job.source.id))
        selected_jobs = due_jobs[:max_jobs]

        logger.info(
            "jobs generated",
            extra={"job_count": len(selected_jobs), "sources": [job.source.name for job in selected_jobs]},
        )
        logger.info("skipped sources", extra={"sources": skipped_sources})
        logger.info("due sources", extra={"sources": due_sources})
        return selected_jobs

    def _is_due(self, source: Source, now: datetime) -> bool:
        """Return ``True`` when a source should be crawled now."""
        if source.last_crawled is None:
            return True

        last_crawled = self._coerce_datetime(source.last_crawled)
        interval = self._get_frequency_delta(source.crawl_frequency)
        return last_crawled + interval <= now

    def _build_job(self, source: Source, now: datetime) -> CrawlJob:
        """Create a ``CrawlJob`` for a due source."""
        reason = "No previous crawl" if source.last_crawled is None else "Due based on crawl frequency"
        return CrawlJob(
            source=source,
            priority=source.priority,
            scheduled_time=now,
            reason=reason,
        )

    def _get_frequency_delta(self, crawl_frequency: str) -> timedelta:
        """Convert a supported crawl frequency string into a ``timedelta``."""
        normalized = crawl_frequency.strip().lower()
        if normalized not in self._FREQUENCY_MAP:
            raise ValueError(f"Unsupported crawl frequency: {crawl_frequency}")
        return self._FREQUENCY_MAP[normalized]

    def _coerce_datetime(self, value: datetime) -> datetime:
        """Normalize datetimes so comparisons remain consistent."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def _get_now(self) -> datetime:
        """Return the current time for scheduling decisions."""
        return datetime.now(timezone.utc)
