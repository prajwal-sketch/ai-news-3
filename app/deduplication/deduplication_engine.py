"""Deduplication engine for comparing parsed articles against existing ones."""

from __future__ import annotations

import hashlib
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Iterable, Optional, Sequence
from uuid import UUID

from app.models.article import Article
from app.deduplication.models import DeduplicationResult

logger = logging.getLogger(__name__)


class DeduplicationEngine:
    """Decide whether a parsed article duplicates an existing article.

    The engine is intentionally limited to deterministic checks. Semantic checks
    can be added later through additional strategies without changing the public
    API.
    """

    def __init__(self) -> None:
        self._strategies: Sequence["DeduplicationStrategy"] = (
            self._check_url_match,
            self._check_title_match,
            self._check_content_hash,
        )

    def check(self, article: Article, existing_articles: Iterable[Article]) -> DeduplicationResult:
        """Compare an article against a collection of existing articles."""
        started_at = time.perf_counter()
        logger.info("comparison count", extra={"count": len(list(existing_articles))})

        normalized_content = self._normalize_content(article.content)
        content_hash = self._hash_content(normalized_content)
        logger.info("hash generation", extra={"hash": content_hash})

        existing_list = list(existing_articles)
        logger.info("comparison count", extra={"count": len(existing_list)})

        for existing in existing_list:
            for strategy in self._strategies:
                match = strategy(article, existing, content_hash)
                if match is not None:
                    duration = time.perf_counter() - started_at
                    logger.info("duplicate detected", extra={"reason": match["reason"], "duration": duration})
                    return DeduplicationResult(
                        is_duplicate=True,
                        reason=match["reason"],
                        matched_article_id=existing.id,
                        content_hash=content_hash,
                        checked_at=datetime.now(timezone.utc),
                    )

        duration = time.perf_counter() - started_at
        logger.info("new article", extra={"duration": duration, "hash": content_hash})
        return DeduplicationResult(
            is_duplicate=False,
            reason="new_article",
            matched_article_id=None,
            content_hash=content_hash,
            checked_at=datetime.now(timezone.utc),
        )

    def _check_url_match(self, article: Article, existing: Article, content_hash: str) -> Optional[dict[str, Any]]:
        if article.url and existing.url and article.url == existing.url:
            return {"reason": "url_match"}
        return None

    def _check_title_match(self, article: Article, existing: Article, content_hash: str) -> Optional[dict[str, Any]]:
        if self._normalize_text(article.title) and self._normalize_text(existing.title):
            if self._normalize_text(article.title).lower() == self._normalize_text(existing.title).lower():
                return {"reason": "title_match"}
        return None

    def _check_content_hash(self, article: Article, existing: Article, content_hash: str) -> Optional[dict[str, Any]]:
        existing_hash = self._hash_content(self._normalize_content(existing.content))
        if content_hash == existing_hash:
            return {"reason": "content_hash_match"}
        return None

    def _normalize_content(self, content: str) -> str:
        """Normalize content for hashing."""
        if not content:
            return ""
        normalized = content.strip().lower()
        return re.sub(r"\s+", " ", normalized)

    def _normalize_text(self, value: str) -> str:
        """Normalize text for comparison."""
        return re.sub(r"\s+", " ", (value or "")).strip()

    def _hash_content(self, content: str) -> str:
        """Create a SHA-256 hash for normalized content."""
        logger.info("hash generation", extra={"content_length": len(content)})
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


DeduplicationStrategy = Any
