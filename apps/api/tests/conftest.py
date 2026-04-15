from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://test")

from app.main import app


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        self._store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> int:
        return int(self._store.pop(key, None) is not None)


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    redis_client = FakeRedis()
    monkeypatch.setattr("app.main.redis.from_url", MagicMock(return_value=redis_client))
    return redis_client


@pytest.fixture(autouse=True)
def fake_db_pool(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_pool = MagicMock()
    mock_pool.close = AsyncMock()
    monkeypatch.setattr("app.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool))
    return mock_pool


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=True)
