from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app.config.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "env": settings.app_env,
        "version": settings.app_version,
        "time": datetime.now(UTC).isoformat(),
    }
