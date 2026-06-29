from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from app.models.article import Article
from app.models.crawl_job import CrawlJob
from app.models.crawl_result import CrawlResult
from app.models.extraction_result import ExtractionResult
from app.models.source import Source
from app.services.pipeline_service import PipelineService


class DummyRepository:
    def __init__(self) -> None:
        self.saved: List[Article] = []

    def save(self, article: Article) -> None:
        self.saved.append(article)


class DummyPlaywrightService:
    def crawl(self, job: CrawlJob) -> CrawlResult:
        return CrawlResult(
            source=job.source,
            url=str(job.source.url),
            html="<html><body>ok</body></html>",
            status_code=200,
            fetched_at=datetime.now(timezone.utc),
            response_time=0.1,
            success=True,
            error_message=None,
        )


class DummyExtractionService:
    def extract(self, result: CrawlResult) -> ExtractionResult:
        return ExtractionResult(
            source=result.source,
            url=result.url,
            title="Example",
            markdown="Sample article",
            metadata={},
            links=[],
            images=[],
            extracted_at=datetime.now(timezone.utc),
            success=True,
            error_message=None,
        )


class DummyParser:
    def parse(self, extraction: ExtractionResult) -> Article:
        return Article(
            id=uuid4(),
            source="Example",
            url=extraction.url,
            title=extraction.title,
            summary="Sample",
            content=extraction.markdown,
            author=None,
            published_at=None,
            category="general",
            tags=[],
            language="en",
            word_count=2,
            scraped_at=datetime.now(timezone.utc),
        )


class DummyDeduplicationEngine:
    def __init__(self, duplicate: bool = False) -> None:
        self.duplicate = duplicate

    def check(self, article: Article, existing_articles: list[Article]) -> object:
        class Result:
            def __init__(self, duplicate: bool) -> None:
                self.is_duplicate = duplicate
                self.reason = "duplicate" if duplicate else "new_article"

        return Result(self.duplicate)


class DummyScheduler:
    def __init__(self, jobs: list[CrawlJob]) -> None:
        self._jobs = jobs

    def get_due_jobs(self, max_jobs: int = 3) -> list[CrawlJob]:
        return self._jobs[:max_jobs]


def make_job(name: str) -> CrawlJob:
    source = Source(
        id=1,
        name=name,
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
    return CrawlJob(source=source, priority=1, scheduled_time=datetime.now(timezone.utc), reason="test")


def test_run_processes_jobs_and_continues_after_failure() -> None:
    repo = DummyRepository()
    failing_job = make_job("Failing")
    good_job = make_job("Good")

    scheduler = DummyScheduler([failing_job, good_job])

    class MixedPlaywrightService:
        def __init__(self) -> None:
            self.calls = 0

        def crawl(self, job: CrawlJob) -> CrawlResult:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("boom")
            return CrawlResult(
                source=job.source,
                url=str(job.source.url),
                html="<html><body>ok</body></html>",
                status_code=200,
                fetched_at=datetime.now(timezone.utc),
                response_time=0.1,
                success=True,
                error_message=None,
            )

    service = PipelineService(
        registry=None,  # type: ignore[arg-type]
        scheduler=scheduler,
        playwright_service=MixedPlaywrightService(),
        extraction_service=DummyExtractionService(),
        parser=DummyParser(),
        deduplication_engine=DummyDeduplicationEngine(duplicate=False),
        repository=repo,
        max_jobs=2,
    )

    result = service.run()

    assert result.jobs_processed == 2
    assert result.failed == 1
    assert result.successful == 1
    assert result.saved_articles == 1
