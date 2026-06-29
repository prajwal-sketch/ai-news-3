"""Parser package exports."""

from app.models.article import Article
from app.parser.article_parser import ArticleParser

__all__ = ["Article", "ArticleParser"]
