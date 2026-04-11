from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 数据库
    database_url: str = Field(alias="DATABASE_URL")

    # CORS
    cors_origins: list[str] = Field(default=[
        "http://localhost:5173",  # Web app
        "http://localhost:5174",  # Admin app
    ])

    # 应用
    app_env: str = "development"
    app_version: str = "1.0.0"

    # Task worker
    task_worker_poll_interval_seconds: float = 1.0
    task_worker_heartbeat_interval_seconds: float = 5.0
    task_worker_stale_timeout_seconds: float = 60.0

    model_config = SettingsConfigDict(
        env_file=".env.development",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
