from __future__ import annotations

from datetime import datetime, timezone

from app.models.extraction_result import ExtractionResult
from app.parser import ArticleParser


def test_parse_normalizes_extraction_into_article() -> None:
    extraction = ExtractionResult(
        source="Example",
        url="https://example.com/news",
        title="  Example Title  ",
        markdown="# Example\n\nThis is   a  sample article.\n\nAnother line.",
        metadata={
            "author": " Jane Doe ",
            "published_at": "2024-05-01T10:30:00Z",
            "category": "Technology",
            "tags": ["AI", "News"],
        },
        links=["https://example.com/about"],
        images=["https://example.com/img.png"],
        extracted_at=datetime.now(timezone.utc),
        success=True,
        error_message=None,
    )

    article = ArticleParser().parse(extraction)

    assert article.title == "Example Title"
    assert article.summary == "This is a sample article."
    assert article.author == "Jane Doe"
    assert article.published_at is not None
    assert article.category == "technology"
    assert article.word_count == 7
    assert article.content.startswith("This is a sample article")
