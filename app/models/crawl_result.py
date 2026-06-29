"""Shared crawl result model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CrawlResult(BaseModel):
    """Result of a single Playwright-driven crawl request."""

    source: Any = Field(..., description="Source identifier or object")
    url: str = Field(..., description="Fetched URL")
    html: str = Field(default="", description="Rendered HTML payload")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    fetched_at: datetime = Field(..., description="When the crawl completed")
    response_time: float = Field(..., description="Response time in seconds")
    success: bool = Field(..., description="Whether the fetch succeeded")
    error_message: Optional[str] = Field(None, description="Failure reason if any")
