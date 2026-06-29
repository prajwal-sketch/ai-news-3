"""Pipeline API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_pipeline_service
from app.api.schemas import PipelineStatusResponse
from app.services.pipeline_service import PipelineResult, PipelineService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run", response_model=PipelineStatusResponse, summary="Run one pipeline cycle", description="Execute a complete crawl, extraction, parsing, and deduplication cycle.")
def run_pipeline(
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineStatusResponse:
    """Execute the pipeline and return the run summary."""
    try:
        result = service.run()
    except Exception as exc:  # pragma: no cover - defensive boundary
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return PipelineStatusResponse.model_validate(result.model_dump())


@router.get("/status", response_model=PipelineStatusResponse, summary="Get latest pipeline status", description="Return the latest pipeline statistics if available.")
def pipeline_status(
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineStatusResponse:
    """Return the latest pipeline statistics."""
    if not hasattr(service, "last_result"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no pipeline run recorded")
    return PipelineStatusResponse.model_validate(service.last_result.model_dump())
