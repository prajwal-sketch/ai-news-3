from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from app.crawler import CrawlResult, PlaywrightService
from app.models.crawl_job import CrawlJob
from app.models.source import Source


class DummyResponse:
    def __init__(self, status: int = 200) -> None:
        self.status = status


class DummyPage:
    def __init__(self, html: str = "<html>ok</html>") -> None:
        self.html_content = html
        self.closed = False

    def goto(self, url: str, wait_until: str, timeout: int) -> DummyResponse:
        self.last_url = url
        self.last_wait_until = wait_until
        self.last_timeout = timeout
        return DummyResponse(status=200)

    def content(self) -> str:
        return self.html_content

    def close(self) -> None:
        self.closed = True


class DummyContext:
    def __init__(self, page: DummyPage) -> None:
        self.page = page
        self.closed = False

    def new_page(self) -> DummyPage:
        return self.page

    def close(self) -> None:
        self.closed = True


class DummyBrowser:
    def __init__(self, page: DummyPage) -> None:
        self.page = page
        self.closed = False

    def new_context(self) -> DummyContext:
        return DummyContext(self.page)

    def close(self) -> None:
        self.closed = True


class DummyChromium:
    def __init__(self, page: DummyPage) -> None:
        self.page = page

    def launch(self, headless: bool) -> DummyBrowser:
        return DummyBrowser(self.page)


class DummyPlaywright:
    def __init__(self, page: DummyPage) -> None:
        self.chromium = DummyChromium(page)


def make_job() -> CrawlJob:
    source = Source(
        id=1,
        name="Example",
        url="https://example.com",
        crawler="playwright",
        parser="html_parser",
        crawl_frequency="1h",
        enabled=True,
        priority=1,
        category="AI",
        allowed_paths=["/"],
        last_crawled=None,
    )
    return CrawlJob(
        source=source,
        priority=1,
        scheduled_time=datetime.now(timezone.utc),
        reason="test",
    )


def test_crawl_returns_rendered_html_and_success_flag() -> None:
    page = DummyPage("<html><body>rendered</body></html>")
    dummy_playwright = DummyPlaywright(page)

    with patch("app.crawler.playwright_service.sync_playwright", return_value=[dummy_playwright]):
        service = PlaywrightService()
        result = service.crawl(make_job())

    assert result.success is True
    assert result.html == "<html><body>rendered</body></html>"
    assert result.status_code == 200
    assert result.source.name == "Example"


def test_crawl_returns_failure_result_without_crashing() -> None:
    class BrokenPage:
        def goto(self, url: str, wait_until: str, timeout: int) -> None:
            raise TimeoutError("slow")

    dummy_playwright = DummyPlaywright(BrokenPage())

    with patch("app.crawler.playwright_service.sync_playwright", return_value=[dummy_playwright]):
        service = PlaywrightService(timeout_ms=1)
        result = service.crawl(make_job())

    assert result.success is False
    assert result.error_message is not None
    assert result.html == ""
