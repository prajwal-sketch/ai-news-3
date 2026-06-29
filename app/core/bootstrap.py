"""Application bootstrap helpers for assembling the platform."""

from __future__ import annotations

import logging
from typing import Any

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers.articles import router as articles_router
from app.api.routers.health import router as health_router
from app.api.routers.pipeline import router as pipeline_router
from app.api.routers.sources import router as sources_router
from app.config.settings import settings
from app.core.dependencies import get_article_repository, get_pipeline, get_registry, get_scheduler, get_source_repository
from app.core.lifecycle import ApplicationLifecycle
from app.core.logging_config import configure_logging
from app.crawler.crawl4ai_service import Crawl4AIService
from app.crawler.playwright_service import PlaywrightService
from app.database.database import DatabaseManager
from app.database.repositories.article_repository import ArticleRepository
from app.database.repositories.source_repository import SourceRepository
from app.deduplication.deduplication_engine import DeduplicationEngine
from app.parser.article_parser import ArticleParser
from app.registry.source_registry import SourceRegistry
from app.scheduler.scheduler import Scheduler
from app.services.pipeline_service import PipelineService

logger = logging.getLogger("application")


def create_application() -> FastAPI:
    """Create and configure the full FastAPI application instance."""
    configure_logging()

    database_manager = DatabaseManager(settings.DATABASE_URL)
    registry = SourceRegistry(settings.SOURCE_REGISTRY)
    scheduler = Scheduler(registry)
    playwright_service = PlaywrightService()
    extraction_service = Crawl4AIService()
    parser = ArticleParser()
    deduplication_engine = DeduplicationEngine()
    article_repository = ArticleRepository(lambda: database_manager.get_session())
    source_repository = SourceRepository(lambda: database_manager.get_session())
    pipeline_service = PipelineService(
        registry=registry,
        scheduler=scheduler,
        playwright_service=playwright_service,
        extraction_service=extraction_service,
        parser=parser,
        deduplication_engine=deduplication_engine,
        repository=article_repository,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        lifecycle.on_startup(app)
        try:
            yield
        finally:
            lifecycle.on_shutdown(app)

    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
    lifecycle = ApplicationLifecycle(database_manager=database_manager, registry=registry)

    app.state.container = {
        "database_manager": database_manager,
        "registry": registry,
        "scheduler": scheduler,
        "article_repository": article_repository,
        "source_repository": source_repository,
        "pipeline_service": pipeline_service,
    }

    app.include_router(health_router)
    app.include_router(articles_router)
    app.include_router(sources_router)
    app.include_router(pipeline_router)

    logger.info("application created")
    return app
