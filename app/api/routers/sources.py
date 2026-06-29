"""Source API routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_source_repository
from app.api.schemas import SourceResponse
from app.database.repositories.source_repository import SourceRepository
from app.models.source import Source

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=List[SourceResponse], summary="List configured sources", description="Return the configured sources from the repository.")
def list_sources(
    repository: SourceRepository = Depends(get_source_repository),
) -> List[SourceResponse]:
    """Return configured sources."""
    return [SourceResponse.model_validate(source.model_dump()) for source in repository.list_sources()]


@router.put("/{source_id}/enable", response_model=SourceResponse, summary="Enable a source", description="Enable a configured source and return the updated record.")
def enable_source(
    source_id: int,
    repository: SourceRepository = Depends(get_source_repository),
) -> SourceResponse:
    """Enable a source."""
    source = repository.get_source(str(source_id))
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source not found")
    source.enabled = True
    repository.save(source)
    return SourceResponse.model_validate(source.model_dump())


@router.put("/{source_id}/disable", response_model=SourceResponse, summary="Disable a source", description="Disable a configured source and return the updated record.")
def disable_source(
    source_id: int,
    repository: SourceRepository = Depends(get_source_repository),
) -> SourceResponse:
    """Disable a source."""
    source = repository.get_source(str(source_id))
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source not found")
    source.enabled = False
    repository.save(source)
    return SourceResponse.model_validate(source.model_dump())
