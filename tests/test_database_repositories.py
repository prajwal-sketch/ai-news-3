from __future__ import annotations

from datetime import datetime, timezone

from app.database.database import DatabaseManager
from app.database.repositories.article_repository import ArticleRepository
from app.models.article import Article


def test_article_repository_round_trip() -> None:
    manager = DatabaseManager("sqlite:///:memory:")
    manager.initialize()

    repository = ArticleRepository(lambda: manager.get_session())
    article = Article(
        source="Example",
        url="https://example.com/article",
        title="Example Article",
        summary="Summary",
        content="Body content",
        author="Author",
        published_at=datetime.now(timezone.utc),
        category="general",
        tags=["news"],
        language="en",
        word_count=3,
        scraped_at=datetime.now(timezone.utc),
    )

    saved = repository.save(article)
    loaded = repository.get_article(article.id)

    assert saved.id == article.id
    assert loaded is not None
    assert loaded.url == article.url
    assert loaded.title == article.title
