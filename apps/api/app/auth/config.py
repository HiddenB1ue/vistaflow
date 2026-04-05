from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    ADMIN_TOKEN: str = ""

    model_config = SettingsConfigDict(
        env_file=".env.development",
        env_file_encoding="utf-8",
        extra="ignore",
    )


auth_settings = AuthSettings()
