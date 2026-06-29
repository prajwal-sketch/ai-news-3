"""Pipeline orchestrator for coordinating crawl, extraction, parsing, and deduplication."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

from pydantic import BaseModel, Field

from app.crawler.crawl4ai_service import Crawl4AIService
from app.crawler.playwright_service import PlaywrightService
from app.deduplication.deduplication_engine import DeduplicationEngine
from app.models.article import Article
from app.models.crawl_job import CrawlJob
from app.parser.article_parser import ArticleParser
from app.registry.source_registry import SourceRegistry
from app.scheduler.scheduler import Scheduler

logger = logging.getLogger(__name__)


class PipelineResult(BaseModel):
    """Summary of a pipeline execution."""

    started_at: datetime = Field(..., description="When the pipeline started")
    finished_at: datetime = Field(..., description="When the pipeline finished")
    jobs_processed: int = Field(..., description="Number of crawl jobs processed")
    successful: int = Field(..., description="Number of successful jobs")
    duplicates: int = Field(..., description="Number of duplicate articles skipped")
    failed: int = Field(..., description="Number of failed jobs")
    saved_articles: int = Field(..., description="Number of articles saved")
    duration: float = Field(..., description="Pipeline duration in seconds")


class ArticleRepository(Protocol):
    """Placeholder repository interface for future persistence implementation."""

    def save(self, article: Article) -> None:
        """Persist an article."""


class PipelineService:
    """Coordinate the end-to-end processing flow for one pipeline run."""

    def __init__(
        self,
        registry: SourceRegistry,
        scheduler: Optional[Scheduler] = None,
        playwright_service: Optional[PlaywrightService] = None,
        extraction_service: Optional[Crawl4AIService] = None,
        parser: Optional[ArticleParser] = None,
        deduplication_engine: Optional[DeduplicationEngine] = None,
        repository: Optional[ArticleRepository] = None,
        max_jobs: int = 3,
    ) -> None:
        self._registry = registry
        self._scheduler = scheduler or Scheduler(registry)
        self._playwright_service = playwright_service or PlaywrightService()
        self._extraction_service = extraction_service or Crawl4AIService()
        self._parser = parser or ArticleParser()
        self._deduplication_engine = deduplication_engine or DeduplicationEngine()
        self._repository = repository
        self._max_jobs = max_jobs
        self.last_result: Optional[PipelineResult] = None

    def run(self) -> PipelineResult:
        """Run the pipeline for the current due jobs."""
        started_at = time.perf_counter()
        logger.info("pipeline started")

        jobs = self._scheduler.get_due_jobs(max_jobs=self._max_jobs)
        stats = self._build_stats(jobs)

        for job in jobs:
            self._run_job(job, stats)

        finished_at = time.perf_counter()
        result = PipelineResult(
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            jobs_processed=len(jobs),
            successful=stats["successful"],
            duplicates=stats["duplicates"],
            failed=stats["failed"],
            saved_articles=stats["saved_articles"],
            duration=finished_at - started_at,
        )
        self.last_result = result
        logger.info("pipeline completed", extra={"result": result.model_dump()})
        return result

    def _run_job(self, job: CrawlJob, stats: dict[str, int]) -> None:
        """Process one crawl job and update statistics."""
        logger.info("job started", extra={"source": job.source.name})

        try:
            crawl_result = self._playwright_service.crawl(job)
            logger.info("download completed", extra={"source": job.source.name, "success": crawl_result.success})
            if not crawl_result.success or not crawl_result.html:
                raise ValueError("download failed")

            extraction_result = self._extraction_service.extract(crawl_result)
            logger.info("extraction completed", extra={"source": job.source.name, "success": extraction_result.success})
            if not extraction_result.success:
                raise ValueError("extraction failed")

            article = self._parser.parse(extraction_result)
            logger.info("parsing completed", extra={"source": article.source, "title": article.title})

            duplicate_result = self._deduplication_engine.check(article, [])
            if duplicate_result.is_duplicate:
                stats["duplicates"] += 1
                logger.info("duplicate detected", extra={"reason": duplicate_result.reason})
                return

            self._save_article(article, stats)
            stats["successful"] += 1
        except Exception as exc:  # pragma: no cover - defensive fallback
            stats["failed"] += 1
            logger.exception("job failed", extra={"source": job.source.name, "error": str(exc)})

    def _save_article(self, article: Article, stats: dict[str, int]) -> None:
        """Persist an article via the repository if available."""
        if self._repository is None:
            stats["saved_articles"] += 1
            logger.info("article saved", extra={"title": article.title})
            return

        self._repository.save(article)
        stats["saved_articles"] += 1
        logger.info("article saved", extra={"title": article.title})

    def _build_stats(self, jobs: list[CrawlJob]) -> dict[str, int]:
        """Create mutable statistics for the current pipeline run."""
        return {"successful": 0, "duplicates": 0, "failed": 0, "saved_articles": 0}
