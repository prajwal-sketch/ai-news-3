"""Shared extraction result model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    """Structured extraction result generated from crawled HTML."""

    source: Any = Field(..., description="Source identifier or object")
    url: str = Field(..., description="Original source URL")
    title: str = Field(default="", description="Extracted article title")
    markdown: str = Field(default="", description="Extracted markdown content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata")
    links: List[str] = Field(default_factory=list, description="Extracted internal/external links")
    images: List[str] = Field(default_factory=list, description="Extracted image URLs")
    extracted_at: datetime = Field(..., description="When extraction completed")
    success: bool = Field(..., description="Whether extraction succeeded")
    error_message: Optional[str] = Field(None, description="Failure reason if any")
