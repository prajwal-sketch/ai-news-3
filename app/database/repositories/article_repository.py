"""Repository for article persistence operations."""

from __future__ import annotations

import hashlib
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models import ArticleORM
from app.models.article import Article

logger = logging.getLogger(__name__)


class ArticleRepository:
    """Persist and query article records."""

    def __init__(self, session_factory: callable) -> None:
        self._session_factory = session_factory

    def save(self, article: Article) -> Article:
        """Persist an article and return it."""
        session = self._session_factory()
        try:
            orm_article = ArticleORM(
                id=article.id,
                source=article.source,
                url=article.url,
                title=article.title,
                summary=article.summary,
                content=article.content,
                author=article.author,
                published_at=article.published_at,
                category=article.category,
                tags=article.tags,
                word_count=article.word_count,
                scraped_at=article.scraped_at,
                content_hash=self._hash_content(article),
            )
            session.add(orm_article)
            session.commit()
            logger.info("article saved")
            return article
        except IntegrityError as exc:
            session.rollback()
            logger.exception("constraint violation", extra={"error": str(exc)})
            raise
        except SQLAlchemyError as exc:
            session.rollback()
            logger.exception("database connection failed", extra={"error": str(exc)})
            raise
        finally:
            session.close()

    def save_article(self, article: Article) -> Article:
        """Backward-compatible alias for save."""
        return self.save(article)

    def get_article(self, article_id: UUID) -> Optional[Article]:
        """Return an article by its identifier."""
        session = self._session_factory()
        try:
            orm_article = session.get(ArticleORM, article_id)
            if orm_article is None:
                return None
            return self._to_domain(orm_article)
        finally:
            session.close()

    def get_latest_articles(self, limit: int = 10) -> List[Article]:
        """Return the latest articles."""
        session = self._session_factory()
        try:
            orm_articles = session.query(ArticleORM).order_by(ArticleORM.scraped_at.desc()).limit(limit).all()
            return [self._to_domain(item) for item in orm_articles]
        finally:
            session.close()

    def search_articles(self, query: str) -> List[Article]:
        """Search articles by title or content."""
        session = self._session_factory()
        try:
            orm_articles = session.query(ArticleORM).filter(
                ArticleORM.title.ilike(f"%{query}%") | ArticleORM.content.ilike(f"%{query}%")
            ).all()
            return [self._to_domain(item) for item in orm_articles]
        finally:
            session.close()

    def article_exists(self, article_url: str) -> bool:
        """Return whether an article with the given URL exists."""
        session = self._session_factory()
        try:
            return session.query(ArticleORM).filter(ArticleORM.url == article_url).first() is not None
        finally:
            session.close()

    def article_exists_hash(self, content_hash: str) -> bool:
        """Return whether an article with the given content hash exists."""
        session = self._session_factory()
        try:
            return session.query(ArticleORM).filter(ArticleORM.content_hash == content_hash).first() is not None
        finally:
            session.close()

    def _hash_content(self, article: Article) -> str:
        """Create a stable content hash for deduplication."""
        payload = f"{article.url}|{article.title}|{article.content}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _to_domain(self, orm_article: ArticleORM) -> Article:
        """Convert an ORM article to the domain model."""
        return Article(
            id=orm_article.id,
            source=orm_article.source,
            url=orm_article.url,
            title=orm_article.title,
            summary=orm_article.summary,
            content=orm_article.content,
            author=orm_article.author,
            published_at=orm_article.published_at,
            category=orm_article.category,
            tags=orm_article.tags or [],
            language="en",
            word_count=orm_article.word_count,
            scraped_at=orm_article.scraped_at,
        )
