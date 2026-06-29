"""Shared source model definitions."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class CrawlerType(str, Enum):
    """Crawler implementation names."""

    PLAYWRIGHT = "playwright"
    API = "api"
    SIMPLE = "simple_crawler"
    RSS = "rss_crawler"


class ParserType(str, Enum):
    """Parser implementation names."""

    HTML = "html_parser"
    RSS = "rss_parser"


class CategoryType(str, Enum):
    """Supported source categories."""

    AI = "AI"


class Source(BaseModel):
    """Typed representation of a news source entry."""

    id: int = Field(..., description="Unique numeric source identifier")
    name: str = Field(..., description="Human readable name")
    url: HttpUrl = Field(..., description="Base URL for the source")
    crawler: CrawlerType = Field(..., description="Crawler implementation name")
    parser: ParserType = Field(..., description="Parser implementation name")
    crawl_frequency: str = Field(..., description="How often to crawl, e.g. daily")
    enabled: bool = Field(..., description="Whether the source is enabled")
    priority: int = Field(..., description="Priority for ordering sources")
    category: CategoryType = Field(..., description="Category label")
    allowed_paths: List[str] = Field(..., description="Allowed URL paths to crawl")
    last_crawled: Optional[datetime] = Field(None, description="ISO timestamp of last crawl")
