from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.deduplication import DeduplicationEngine
from app.models.article import Article


def make_article(title: str, content: str, url: str) -> Article:
    return Article(
        id=uuid4(),
        source="Example",
        url=url,
        title=title,
        summary=content[:80],
        content=content,
        author="Jane",
        published_at=datetime.now(timezone.utc),
        category="general",
        tags=["news"],
        language="en",
        word_count=3,
        scraped_at=datetime.now(timezone.utc),
    )


def test_check_detects_duplicate_by_url() -> None:
    engine = DeduplicationEngine()
    article = make_article("A", "Alpha beta", "https://example.com/a")
    existing = make_article("B", "Gamma", "https://example.com/a")

    result = engine.check(article, [existing])

    assert result.is_duplicate is True
    assert result.reason == "url_match"
    assert result.matched_article_id == existing.id


def test_check_detects_duplicate_by_title_case_insensitive() -> None:
    engine = DeduplicationEngine()
    article = make_article("Same Title", "Alpha", "https://example.com/one")
    existing = make_article("same title", "Other", "https://example.com/two")

    result = engine.check(article, [existing])

    assert result.is_duplicate is True
    assert result.reason == "title_match"


def test_check_detects_duplicate_by_content_hash() -> None:
    engine = DeduplicationEngine()
    article = make_article("New", "Hello world from here", "https://example.com/new")
    existing = make_article("Other", "Hello world from here", "https://example.com/other")

    result = engine.check(article, [existing])

    assert result.is_duplicate is True
    assert result.reason == "content_hash_match"
