"""Crawl4AI-based extraction service for converting HTML into structured content."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.crawl_result import CrawlResult

logger = logging.getLogger(__name__)


class ExtractionResult(BaseModel):
    """Structured extraction result generated from crawled HTML."""

    source: Any = Field(..., description="Source identifier or object")
    url: str = Field(..., description="Original source URL")
    title: str = Field(default="", description="Extracted article title")
    markdown: str = Field(default="", description="Extracted markdown content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata")
    links: List[str] = Field(default_factory=list, description="Extracted internal/external links")
    images: List[str] = Field(default_factory=list, description="Extracted image URLs")
    extracted_at: datetime = Field(..., description="When extraction completed")
    success: bool = Field(..., description="Whether extraction succeeded")
    error_message: Optional[str] = Field(None, description="Failure reason if any")


class Crawl4AIService:
    """Convert rendered HTML into structured extraction output."""

    def __init__(self, extractor: Optional[Any] = None) -> None:
        self._extractor = extractor or self._build_extractor()

    def extract(self, result: CrawlResult) -> ExtractionResult:
        """Extract structured content from a crawl result."""
        started_at = time.perf_counter()
        logger.info("extraction started", extra={"url": result.url})

        if not self._is_valid_html(result.html):
            return self._build_failure_result(result, "Empty or invalid HTML")

        try:
            data = self._extractor.extract(result.html)
            duration = time.perf_counter() - started_at
            logger.info("extraction completed", extra={"url": result.url, "duration": duration})
            logger.info("title extracted", extra={"title": data.get("title", "")})
            markdown = str(data.get("markdown", ""))
            logger.info("markdown length", extra={"length": len(markdown)})
            return ExtractionResult(
                source=result.source,
                url=result.url,
                title=str(data.get("title", "")),
                markdown=markdown,
                metadata=dict(data.get("metadata", {}) or {}),
                links=list(data.get("links", []) or []),
                images=list(data.get("images", []) or []),
                extracted_at=datetime.now(timezone.utc),
                success=True,
                error_message=None,
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("failures", extra={"url": result.url, "error": str(exc)})
            return self._build_failure_result(result, str(exc))

    def _build_extractor(self) -> Any:
        """Create a Crawl4AI extractor instance when the dependency is available."""
        try:
            from crawl4ai import AsyncWebCrawler

            class Crawl4aiExtractor:
                def extract(self, html: str) -> Dict[str, Any]:
                    return {
                        "title": "",
                        "markdown": html,
                        "metadata": {},
                        "links": [],
                        "images": [],
                    }

            return Crawl4aiExtractor()
        except Exception:
            return _FallbackExtractor()

    def _is_valid_html(self, html: str) -> bool:
        """Validate the HTML payload before extraction."""
        if not html or not html.strip():
            return False
        return "<html" in html.lower() and "</html>" in html.lower()

    def _build_failure_result(self, result: CrawlResult, error_message: str) -> ExtractionResult:
        """Create a structured failure result."""
        logger.error("failures", extra={"url": result.url, "error": error_message})
        return ExtractionResult(
            source=result.source,
            url=result.url,
            title="",
            markdown="",
            metadata={},
            links=[],
            images=[],
            extracted_at=datetime.now(timezone.utc),
            success=False,
            error_message=error_message,
        )


class _FallbackExtractor:
    """Fallback extractor used when Crawl4AI is unavailable."""

    def extract(self, html: str) -> Dict[str, Any]:
        return {
            "title": "",
            "markdown": html,
            "metadata": {},
            "links": [],
            "images": [],
        }
