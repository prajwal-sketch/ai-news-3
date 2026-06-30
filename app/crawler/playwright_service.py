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


        started_at = time.perf_counter()
        logger.info("browser started", extra={"source": job.source.name})

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )

                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/137.0.0.0 Safari/537.36"
                    )
                )

                page = context.new_page()

                logger.info(
                    "navigation started",
                    extra={"url": str(job.source.url)},
                )

                response = page.goto(
                    str(job.source.url),
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                page.wait_for_timeout(3000)

                logger.info(
                    "navigation completed",
                    extra={"url": str(job.source.url)},
                )

                html = page.content()

                status_code = response.status if response else None

                response_time = time.perf_counter() - started_at

                logger.info(
                    "response time",
                    extra={
                        "source": job.source.name,
                        "seconds": response_time,
                    },
                )

                browser.close()

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

        except Exception as exc:
            logger.exception(
                "playwright failure",
                extra={
                    "source": job.source.name,
                    "error": str(exc),
                },
            )

            return self._build_failure_result(
                job,
                started_at,
                str(exc),
            )

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
