from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 数据库
    database_url: str = Field(alias="DATABASE_URL")

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:5173"])

    # 12306 集成（可选）
    ticket_12306_cookie: str = ""
    ticket_12306_endpoint: str = "queryG"

    # 高德地图（可选）
    amap_api_key: str = ""

    # 应用
    app_env: str = "development"
    app_version: str = "1.0.0"

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
