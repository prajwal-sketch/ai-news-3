from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import create_app
from app.api.dependencies import get_article_repository, get_pipeline_service, get_source_registry
from app.models.article import Article
from app.services.pipeline_service import PipelineResult


class StubArticleRepository:
    def __init__(self) -> None:
        self._article = Article(
            id=uuid4(),
            source="Example",
            url="https://example.com/articles/1",
            title="Example Article",
            summary="Summary",
            content="Body",
            author="Author",
            published_at=datetime.now(timezone.utc),
            category="general",
            tags=["news"],
            language="en",
            word_count=2,
            scraped_at=datetime.now(timezone.utc),
        )

    def get_latest_articles(self, limit: int = 10) -> list[Article]:
        return [self._article]

    def get_article(self, article_id: object) -> Article | None:
        return self._article if str(self._article.id) == str(article_id) else None

    def search_articles(self, query: str) -> list[Article]:
        return [self._article] if query.lower() in self._article.title.lower() else []


class StubPipelineService:
    def run(self) -> PipelineResult:
        now = datetime.now(timezone.utc)
        return PipelineResult(
            started_at=now,
            finished_at=now,
            jobs_processed=1,
            successful=1,
            duplicates=0,
            failed=0,
            saved_articles=1,
            duration=0.01,
        )


def test_health_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_articles_endpoint_uses_repository() -> None:
    app = create_app()
    app.dependency_overrides[get_article_repository] = lambda: StubArticleRepository()
    app.dependency_overrides[get_pipeline_service] = lambda: StubPipelineService()
    app.dependency_overrides[get_source_registry] = lambda: None

    with TestClient(app) as client:
        response = client.get("/articles")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Example Article"
