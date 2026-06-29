"""Deduplication package for deciding whether an article is already known."""

from app.deduplication.deduplication_engine import DeduplicationEngine
from app.deduplication.models import DeduplicationResult

__all__ = ["DeduplicationEngine", "DeduplicationResult"]
