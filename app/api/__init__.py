"""FastAPI application package for the AI News Intelligence Platform."""

from fastapi import FastAPI

from app.api.dependencies import LoggingMiddleware, configure_dependencies


app: FastAPI | None = None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    global app
    if app is None:
        from app.core.bootstrap import create_application

        app = create_application()
        app.add_middleware(LoggingMiddleware)
        configure_dependencies(app)
    return app
