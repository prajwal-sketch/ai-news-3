"""Dependency providers for the application bootstrap layer."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.database.repositories.article_repository import ArticleRepository
from app.database.repositories.source_repository import SourceRepository
from app.registry.source_registry import SourceRegistry
from app.scheduler.scheduler import Scheduler
from app.services.pipeline_service import PipelineService


def get_container(request: Request) -> dict[str, Any]:
    """Return the application container stored on the request state."""
    return request.app.state.container


def get_registry(request: Request) -> SourceRegistry:
    """Provide the source registry from application state."""
    return get_container(request)["registry"]


def get_scheduler(request: Request) -> Scheduler:
    """Provide the scheduler from application state."""
    return get_container(request)["scheduler"]


def get_article_repository(request: Request) -> ArticleRepository:
    """Provide the article repository from application state."""
    return get_container(request)["article_repository"]


def get_source_repository(request: Request) -> SourceRepository:
    """Provide the source repository from application state."""
    return get_container(request)["source_repository"]


def get_pipeline(request: Request) -> PipelineService:
    """Provide the pipeline service from application state."""
    return get_container(request)["pipeline_service"]
