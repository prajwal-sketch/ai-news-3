"""Repository interface for source persistence."""

from __future__ import annotations

from typing import List, Optional, Protocol

from app.models.source import Source


class SourceRepository(Protocol):
    """Interface for persisting and querying sources."""

    def save(self, source: Source) -> Source:
        """Persist a source and return it."""

    def get_source(self, source_id: str) -> Optional[Source]:
        """Return a source by identifier if present."""

    def list_sources(self) -> List[Source]:
        """Return all configured sources."""
