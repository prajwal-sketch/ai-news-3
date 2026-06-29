"""Health check router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas import HealthStatus

router = APIRouter(prefix="", tags=["health"])


@router.get("/health", response_model=HealthStatus, summary="Health check", description="Return the application health status.")
def health() -> HealthStatus:
    """Return a simple health payload."""
    return HealthStatus(status="ok")
