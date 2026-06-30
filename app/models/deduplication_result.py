"""Shared deduplication result model."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeduplicationResult(BaseModel):
    """Result of a deduplication comparison."""

    is_duplicate: bool = Field(..., description="Whether the article is considered a duplicate")
    reason: str = Field(default="new_article", description="Reason for the decision")
    matched_article_id: Optional[UUID] = Field(None, description="Matched article identifier if duplicate")
    content_hash: str = Field(..., description="SHA-256 hash of the normalized content")
    checked_at: datetime = Field(..., description="When the comparison was performed")
