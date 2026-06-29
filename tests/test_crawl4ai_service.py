from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from app.crawler import CrawlResult
from app.crawler.crawl4ai_service import Crawl4AIService
from app.models.extraction_result import ExtractionResult


def make_result(html: str = "<html><head><title>Example</title></head><body><p>Hello</p></body></html>") -> CrawlResult:
    return CrawlResult(
        source="Example",
        url="https://example.com",
        html=html,
        status_code=200,
        fetched_at=datetime.now(timezone.utc),
        response_time=0.1,
        success=True,
        error_message=None,
    )


def test_extract_returns_structured_content_for_valid_html() -> None:
    extractor = type("Extractor", (), {})()
    extractor.extract = lambda html: {
        "title": "Example",
        "markdown": "# Example\nHello",
        "metadata": {"author": "Test"},
        "links": ["https://example.com/about"],
        "images": ["https://example.com/a.png"],
    }

    service = Crawl4AIService(extractor=extractor)
    result = service.extract(make_result())

    assert result.success is True
    assert result.title == "Example"
    assert result.markdown.startswith("# Example")
    assert result.metadata["author"] == "Test"
    assert result.links == ["https://example.com/about"]
    assert result.images == ["https://example.com/a.png"]


def test_extract_rejects_empty_or_invalid_html() -> None:
    service = Crawl4AIService()
    result = service.extract(make_result(html=""))
    assert result.success is False
    assert result.error_message is not None

    invalid = service.extract(make_result(html="<html><body>not closed"))
    assert invalid.success is False
