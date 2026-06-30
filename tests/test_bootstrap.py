from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.bootstrap import create_application


def test_create_application_returns_fastapi_app() -> None:
    app = create_application()

    assert isinstance(app, FastAPI)
    assert hasattr(app.state, "container")


def test_startup_preserves_container_services() -> None:
    app = create_application()

    with TestClient(app) as client:
        container = app.state.container
        expected_keys = {
            "database_manager",
            "registry",
            "scheduler",
            "article_repository",
            "source_repository",
            "pipeline_service",
        }

        assert expected_keys.issubset(set(container.keys()))
        assert container["database_manager"] is not None
        assert container["registry"] is not None
