"""FastAPI dependency providers for the API layer."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.dependencies import get_article_repository as get_bootstrap_article_repository
from app.core.dependencies import get_pipeline as get_bootstrap_pipeline
from app.core.dependencies import get_registry as get_bootstrap_registry
from app.core.dependencies import get_source_repository as get_bootstrap_source_repository
from app.database.repositories.article_repository import ArticleRepository
from app.database.repositories.source_repository import SourceRepository
from app.registry.source_registry import SourceRegistry
from app.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)


def configure_dependencies(app: FastAPI) -> None:
    """Register centralized error handlers for the API layer."""

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("validation error", extra={"path": request.url.path, "errors": exc.errors()})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.errors()})

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger.warning("http error", extra={"path": request.url.path, "status_code": exc.status_code, "detail": exc.detail})
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error", extra={"path": request.url.path, "error": str(exc)})
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "internal server error"})


def get_article_repository(request: Request) -> ArticleRepository:
    """Provide an article repository from the application container."""
    return get_bootstrap_article_repository(request)


def get_source_repository(request: Request) -> SourceRepository:
    """Provide a source repository from the application container."""
    return get_bootstrap_source_repository(request)


def get_source_registry(request: Request) -> SourceRegistry:
    """Provide a source registry from the application container."""
    return get_bootstrap_registry(request)


def get_pipeline_service(request: Request) -> PipelineService:
    """Provide a pipeline service from the application container."""
    return get_bootstrap_pipeline(request)


class LoggingMiddleware:
    """Middleware that logs incoming requests, execution time, and failures."""

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        started_at = time.perf_counter()
        logger.info("incoming request", extra={"path": request.url.path, "method": request.method})
        try:
            await self.app(scope, receive, send)
        except Exception:
            logger.exception("request failed", extra={"path": request.url.path, "method": request.method})
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            logger.info(
                "endpoint executed",
                extra={"path": request.url.path, "method": request.method, "execution_time_ms": round(elapsed_ms, 3)},
            )
