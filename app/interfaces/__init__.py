"""Interfaces for application services and repositories."""

from app.interfaces.article_repository import ArticleRepository
from app.interfaces.crawl_repository import CrawlRepository
from app.interfaces.source_repository import SourceRepository

__all__ = ["ArticleRepository", "CrawlRepository", "SourceRepository"]
