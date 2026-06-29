"""Parser for transforming extraction results into standardized articles."""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.article import Article
from app.models.extraction_result import ExtractionResult

logger = logging.getLogger(__name__)


class ArticleParser:
    """Normalize extraction output into a consistent article model."""

    def parse(self, extraction: ExtractionResult) -> Article:
        """Transform an extraction result into a normalized article."""
        started_at = time.perf_counter()
        logger.info("parsing started", extra={"source": str(extraction.source), "url": extraction.url})

        cleaned_markdown = self._clean_markdown(extraction.markdown)
        content = self._normalize_whitespace(cleaned_markdown)
        summary = self._build_summary(content)
        author = self._extract_author(extraction.metadata)
        published_at = self._normalize_published_at(extraction.metadata)
        category = self._normalize_category(extraction.metadata, extraction.title)
        tags = self._normalize_tags(extraction.metadata)

        article = Article(
            source=self._stringify_source(extraction.source),
            url=extraction.url,
            title=self._normalize_text(extraction.title) or "Untitled",
            summary=summary,
            content=content,
            author=author,
            published_at=published_at,
            category=category,
            tags=tags,
            language="en",
            word_count=self._count_words(content),
            scraped_at=datetime.now(timezone.utc),
        )

        duration = time.perf_counter() - started_at
        logger.info("parsing completed", extra={"source": article.source, "title": article.title, "word_count": article.word_count, "duration": duration})
        return article

    def _clean_markdown(self, markdown: str) -> str:
        """Remove markdown noise and empty lines while preserving content."""
        if not markdown:
            return ""
        text = re.sub(r"^#{1,6}\s*", "", markdown, flags=re.MULTILINE)
        text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
        text = re.sub(r"[`*_>~-]", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = [line for line in text.splitlines() if line.strip()]
        if lines and re.match(r"^[A-Za-z0-9\s]+$", lines[0]) and len(lines) > 1:
            lines = lines[1:]
        return "\n".join(lines).strip()

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse repeated whitespace and remove blank lines."""
        if not text:
            return ""
        normalized = re.sub(r"[ \t]+", " ", text)
        normalized = re.sub(r"\n\s*\n+", "\n\n", normalized)
        return "\n".join(line.strip() for line in normalized.splitlines() if line.strip())

    def _build_summary(self, content: str) -> str:
        """Return a short summary derived from the parsed content."""
        if not content:
            return ""
        sentences = re.split(r"(?<=[.!?])\s+", content)
        return self._normalize_text(sentences[0])[:280]

    def _extract_author(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract an author from metadata if present."""
        for key in ("author", "byline", "author_name"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return self._normalize_text(value)
        return None

    def _normalize_published_at(self, metadata: Dict[str, Any]) -> Optional[datetime]:
        """Normalize publication dates when available."""
        for key in ("published_at", "date", "published"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return None
        return None

    def _normalize_category(self, metadata: Dict[str, Any], title: str) -> str:
        """Normalize category information into a lowercase slug."""
        for key in ("category", "section"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return self._normalize_text(value).lower().replace(" ", "_")
        if title:
            return "general"
        return "general"

    def _normalize_tags(self, metadata: Dict[str, Any]) -> List[str]:
        """Normalize tags into a list of lowercase strings."""
        tags_value = metadata.get("tags")
        if isinstance(tags_value, list):
            return [self._normalize_text(tag).lower() for tag in tags_value if self._normalize_text(tag)]
        if isinstance(tags_value, str) and tags_value.strip():
            return [tag.strip().lower() for tag in tags_value.split(",") if tag.strip()]
        return []

    def _normalize_text(self, value: str) -> str:
        """Normalize a text field by stripping and collapsing whitespace."""
        return re.sub(r"\s+", " ", value or "").strip()

    def _count_words(self, content: str) -> int:
        """Count words in normalized content."""
        return len(re.findall(r"\b\w+\b", content)) if content else 0

    def _stringify_source(self, source: Any) -> str:
        """Convert the source value to a readable string."""
        if hasattr(source, "name"):
            return str(source.name)
        return str(source)
