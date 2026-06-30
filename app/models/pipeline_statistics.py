"""Pipeline run statistics model."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PipelineStatistics(BaseModel):
    """Mutable counters for a single pipeline execution."""

    successful: int = Field(default=0, description="Number of successful jobs")
    duplicates: int = Field(default=0, description="Number of duplicate articles skipped")
    failed: int = Field(default=0, description="Number of failed jobs")
    saved_articles: int = Field(default=0, description="Number of articles saved")
