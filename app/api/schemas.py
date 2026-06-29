"""Pydantic schemas for FastAPI response models."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Health check payload."""

    status: str = Field("ok", description="Application status")


class ArticleResponse(BaseModel):
    """Serialized article."""

    id: UUID
    source: str
    url: str
    title: str
    summary: str
    content: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    category: str
    tags: List[str]
    language: str
    word_count: int
    scraped_at: datetime


class SourceResponse(BaseModel):
    """Serialized source."""

    id: int
    name: str
    url: str
    crawler: str
    parser: str
    crawl_frequency: str
    enabled: bool
    priority: int
    category: str
    allowed_paths: List[str]
    last_crawled: Optional[datetime] = None


class PipelineStatusResponse(BaseModel):
    """Latest pipeline execution summary."""

    started_at: datetime
    finished_at: datetime
    jobs_processed: int
    successful: int
    duplicates: int
    failed: int
    saved_articles: int
    duration: float
