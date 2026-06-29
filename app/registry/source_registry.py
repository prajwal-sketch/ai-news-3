"""Source registry for AI News Intelligence Platform.

Provides a typed, validated registry for news sources defined in a JSON file.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError

from app.config.settings import settings
from app.models.source import Source

logger = logging.getLogger(__name__)


class SourceRegistryError(Exception):
    """Base exception for source registry errors."""


class MissingSourceFileError(SourceRegistryError):
    """Raised when the sources JSON file cannot be found."""


class InvalidJSONError(SourceRegistryError):
    """Raised when the sources JSON file contains invalid JSON."""


class SchemaValidationError(SourceRegistryError):
    """Raised when a source definition fails schema validation."""


class SourceNotFoundError(SourceRegistryError):
    """Raised when a requested source cannot be found in the registry."""


class SourceRegistry:
    """Manages loading and querying news sources from a JSON registry file.

    The registry does not implement crawling. It only loads, validates and
    exposes source definitions. Only `update_last_crawled` may modify the
    underlying JSON file.
    """

    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        self._path = Path(path) if path is not None else Path(settings.SOURCE_REGISTRY)
        self._sources: List[Source] = self._load()

    def _load(self) -> List[Source]:
        """Load and validate sources from the JSON file."""
        logger.info("Loading source registry", extra={"path": str(self._path)})

        if not self._path.exists():
            message = f"Source registry file not found: {self._path}"
            logger.error(message)
            raise MissingSourceFileError(message)

        raw = self._read_raw_sources()
        if not isinstance(raw, list):
            message = f"Source registry file must contain a JSON list: {self._path}"
            logger.error(message)
            raise InvalidJSONError(message)

        sources = self._parse_sources(raw)
        logger.info(
            "Loaded source registry",
            extra={"path": str(self._path), "sources_count": len(sources)},
        )
        return sources

    def _read_raw_sources(self) -> Any:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            message = f"Invalid JSON in source registry {self._path}: {exc}"
            logger.exception(message)
            raise InvalidJSONError(message)

    def _parse_sources(self, raw_sources: List[Any]) -> List[Source]:
        sources: List[Source] = []
        for index, item in enumerate(raw_sources):
            if not isinstance(item, dict):
                message = f"Source entry at index {index} must be an object"
                logger.error(message)
                raise SchemaValidationError(message)

            try:
                sources.append(Source(**item))
            except ValidationError as exc:
                message = self._format_validation_error(exc, item)
                logger.exception(message)
                raise SchemaValidationError(message)

        return sources

    def _format_validation_error(self, exc: ValidationError, source_data: Dict[str, Any]) -> str:
        first_error = exc.errors()[0] if exc.errors() else {}
        field_name = "unknown"
        if "loc" in first_error and isinstance(first_error["loc"], tuple):
            field_name = str(first_error["loc"][-1])

        source_name = source_data.get("name") or source_data.get("id") or "<unknown>"
        error_message = first_error.get("msg", "validation failed")
        return f"Source '{source_name}' validation failed for field '{field_name}': {error_message}"

    def get_all_sources(self) -> List[Source]:
        """Return all sources (including disabled ones)."""
        logger.debug("Fetching all sources", extra={"source_count": len(self._sources)})
        return list(self._sources)

    def get_enabled_sources(self) -> List[Source]:
        """Return only enabled sources, ordered by priority ascending."""
        enabled_sources = [source for source in self._sources if source.enabled]
        sorted_sources = sorted(enabled_sources, key=lambda source: source.priority)
        logger.debug(
            "Fetching enabled sources",
            extra={"enabled_source_count": len(sorted_sources)},
        )
        return sorted_sources

    def get_source_by_id(self, source_id: int) -> Source:
        """Return a source by its `id` or raise SourceNotFoundError."""
        logger.debug("Looking up source by id", extra={"source_id": source_id})
        for source in self._sources:
            if source.id == source_id:
                return source

        message = f"Source with id '{source_id}' not found"
        logger.warning(message)
        raise SourceNotFoundError(message)

    def get_source_by_name(self, name: str) -> Source:
        """Return a source by its `name` or raise SourceNotFoundError."""
        logger.debug("Looking up source by name", extra={"source_name": name})
        for source in self._sources:
            if source.name == name:
                return source

        message = f"Source with name '{name}' not found"
        logger.warning(message)
        raise SourceNotFoundError(message)

    def update_last_crawled(self, source_id: int, timestamp: Union[str, datetime]) -> None:
        """Update the `last_crawled` timestamp for the source with `id`."""
        if isinstance(timestamp, datetime):
            ts = timestamp.replace(microsecond=0).isoformat()
        else:
            ts = str(timestamp)

        logger.info(
            "Updating source last_crawled",
            extra={"source_id": source_id, "last_crawled": ts},
        )

        raw_sources = self._read_raw_sources()
        if not isinstance(raw_sources, list):
            message = f"Source registry file must contain a JSON list: {self._path}"
            logger.error(message)
            raise InvalidJSONError(message)

        updated = False
        for entry in raw_sources:
            if isinstance(entry, dict) and entry.get("id") == source_id:
                entry["last_crawled"] = ts
                updated = True
                break

        if not updated:
            message = f"Source with id '{source_id}' not found"
            logger.warning(message)
            raise SourceNotFoundError(message)

        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        try:
            tmp_path.write_text(json.dumps(raw_sources, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp_path.replace(self._path)
        except Exception as exc:
            message = f"Failed to write updated source registry file: {exc}"
            logger.exception(message)
            raise SourceRegistryError(message)

        self._sources = self._load()