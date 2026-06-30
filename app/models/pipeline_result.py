"""Shared pipeline execution result model."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PipelineResult(BaseModel):
    """Summary of a pipeline execution."""

    started_at: datetime = Field(..., description="When the pipeline started")
    finished_at: datetime = Field(..., description="When the pipeline finished")
    jobs_processed: int = Field(..., description="Number of crawl jobs processed")
    successful: int = Field(..., description="Number of successful jobs")
    duplicates: int = Field(..., description="Number of duplicate articles skipped")
    failed: int = Field(..., description="Number of failed jobs")
    saved_articles: int = Field(..., description="Number of articles saved")
    duration: float = Field(..., description="Pipeline duration in seconds")
