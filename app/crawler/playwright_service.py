"""Playwright-based HTML fetching service for crawl jobs."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from app.models.crawl_job import CrawlJob

logger = logging.getLogger(__name__)


class CrawlResult(BaseModel):
    """Result of a single Playwright-driven crawl request."""

    source: Any = Field(..., description="Source identifier or object")
    url: str = Field(..., description="Fetched URL")
    html: str = Field(default="", description="Rendered HTML payload")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    fetched_at: datetime = Field(..., description="When the crawl completed")
    response_time: float = Field(..., description="Response time in seconds")
    success: bool = Field(..., description="Whether the fetch succeeded")
    error_message: Optional[str] = Field(None, description="Failure reason if any")


class PlaywrightService:
    """Fetch fully rendered HTML for a crawl job without parsing or persistence."""

    def __init__(self, timeout_ms: int = 30000) -> None:
        self.timeout_ms = timeout_ms

    def crawl(self, job: CrawlJob) -> CrawlResult:
        """Fetch rendered HTML for the given crawl job and return structured result."""
        started_at = time.perf_counter()
        logger.info("browser started", extra={"source": job.source.name})

        try:
            playwright_manager = sync_playwright()
            if hasattr(playwright_manager, "__enter__") and hasattr(playwright_manager, "__exit__"):
                playwright_context = playwright_manager
                playwright = playwright_context.__enter__()
            else:
                playwright_context = None
                playwright = playwright_manager

            if isinstance(playwright, (list, tuple)):
                playwright = playwright[0]

            try:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                try:
                    logger.info("navigation started", extra={"url": str(job.source.url)})
                    response = page.goto(
                        str(job.source.url),
                        wait_until="networkidle",
                        timeout=self.timeout_ms,
                    )
                    logger.info("navigation completed", extra={"url": str(job.source.url)})
                    html = page.content()
                    status_code = getattr(response, "status", None)
                    response_time = time.perf_counter() - started_at
                    logger.info("response time", extra={"source": job.source.name, "seconds": response_time})
                    return CrawlResult(
                        source=job.source,
                        url=str(job.source.url),
                        html=html,
                        status_code=status_code,
                        fetched_at=datetime.now(timezone.utc),
                        response_time=response_time,
                        success=True,
                        error_message=None,
                    )
                finally:
                    page.close()
                    context.close()
                    browser.close()
            finally:
                if playwright_context is not None:
                    playwright_context.__exit__(None, None, None)
        except PlaywrightError as exc:
            logger.exception("playwright failure", extra={"source": job.source.name, "error": str(exc)})
            return self._build_failure_result(job, started_at, str(exc))
        except TimeoutError as exc:
            logger.warning("playwright timeout", extra={"source": job.source.name, "error": str(exc)})
            return self._build_failure_result(job, started_at, str(exc))
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("unexpected playwright failure", extra={"source": job.source.name, "error": str(exc)})
            return self._build_failure_result(job, started_at, str(exc))

    def _build_failure_result(self, job: CrawlJob, started_at: float, error_message: str) -> CrawlResult:
        """Create a failure result without raising exceptions."""
        response_time = time.perf_counter() - started_at
        logger.error("failures", extra={"source": job.source.name, "error": error_message, "seconds": response_time})
        return CrawlResult(
            source=job.source,
            url=str(job.source.url),
            html="",
            status_code=None,
            fetched_at=datetime.now(timezone.utc),
            response_time=response_time,
            success=False,
            error_message=error_message,
        )
