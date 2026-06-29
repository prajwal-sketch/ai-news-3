"""Pydantic models for the scheduler package."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.registry.source_registry import Source


class CrawlJob(BaseModel):
    """Represents a crawl task selected by the scheduler."""

    source: Source = Field(..., description="Source that should be crawled")
    priority: int = Field(..., description="Priority for ordering crawl jobs")
    scheduled_time: datetime = Field(..., description="Time the crawl was scheduled")
    reason: str = Field(..., description="Why the source was selected")
