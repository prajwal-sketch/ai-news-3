from __future__ import annotations

from fastapi import FastAPI

from app.core.bootstrap import create_application


def test_create_application_returns_fastapi_app() -> None:
    app = create_application()

    assert isinstance(app, FastAPI)
    assert hasattr(app.state, "container")
