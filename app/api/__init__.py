"""FastAPI application package for the AI News Intelligence Platform."""

from fastapi import FastAPI

from app.api.dependencies import LoggingMiddleware, configure_dependencies
from app.api.routers.articles import router as articles_router
from app.api.routers.health import router as health_router
from app.api.routers.pipeline import router as pipeline_router
from app.api.routers.sources import router as sources_router
from app.core.bootstrap import create_application


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = create_application()
    app.add_middleware(LoggingMiddleware)
    configure_dependencies(app)
    return app


app = create_app()
