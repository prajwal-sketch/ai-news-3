from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI News Intelligence Platform"
    APP_VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite:///./ai_news.db"
    LOG_LEVEL: str = "INFO"
    SOURCE_REGISTRY: str = "app/config/sources.json"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def sources(self) -> List[dict]:
        path = Path(self.SOURCE_REGISTRY)
        if not path.is_file():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []


settings = Settings()
