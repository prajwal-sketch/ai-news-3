"""Custom exceptions for the application bootstrap layer."""

from __future__ import annotations


class ConfigurationError(Exception):
    """Raised when required configuration is invalid or missing."""


class RegistryError(Exception):
    """Raised when the source registry cannot be initialized or queried."""


class CrawlerError(Exception):
    """Raised when a crawler operation fails."""


class ParserError(Exception):
    """Raised when article parsing fails."""


class PipelineError(Exception):
    """Raised when the pipeline orchestration fails."""


class RepositoryError(Exception):
    """Raised when persistence fails."""
