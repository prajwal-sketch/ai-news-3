"""Repository interface for article persistence."""

from __future__ import annotations

from typing import List, Optional, Protocol
from uuid import UUID

from app.models.article import Article


class ArticleRepository(Protocol):
    """Interface for persisting and querying articles."""

    def save(self, article: Article) -> Article:
        """Persist an article and return it."""

    def get_article(self, article_id: UUID) -> Optional[Article]:
        """Return an article by identifier if present."""

    def get_latest_articles(self, limit: int = 10) -> List[Article]:
        """Return the latest articles."""

    def search_articles(self, query: str) -> List[Article]:
        """Search articles by query."""

    def article_exists(self, article_url: str) -> bool:
        """Return whether an article exists for the given URL."""

    def article_exists_hash(self, content_hash: str) -> bool:
        """Return whether an article exists for the given content hash."""
