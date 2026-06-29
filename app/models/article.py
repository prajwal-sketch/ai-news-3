"""Shared article model."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Article(BaseModel):
    """Normalized article representation used across the application."""

    id: UUID = Field(default_factory=uuid4, description="Unique article identifier")
    source: str = Field(..., description="Source name")
    url: str = Field(..., description="Original article URL")
    title: str = Field(default="", description="Normalized article title")
    summary: str = Field(default="", description="Normalized article summary")
    content: str = Field(default="", description="Normalized article content")
    author: Optional[str] = Field(None, description="Normalized author name")
    published_at: Optional[datetime] = Field(None, description="Normalized publication date")
    category: str = Field(default="general", description="Normalized category")
    tags: List[str] = Field(default_factory=list, description="Normalized tags")
    language: str = Field(default="en", description="Normalized language")
    word_count: int = Field(default=0, description="Word count for normalized content")
    scraped_at: datetime = Field(..., description="When the article was parsed")
