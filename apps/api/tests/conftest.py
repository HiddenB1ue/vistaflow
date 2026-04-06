from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://test")

from app.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    mock_pool = MagicMock()
    mock_pool.close = AsyncMock()
    monkeypatch.setattr("app.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool))
    monkeypatch.setattr("app.main.TaskRunRepository.recover_incomplete_runs", AsyncMock())
    monkeypatch.setattr("app.main.TaskRepository.recover_incomplete_tasks", AsyncMock())
    return TestClient(app, raise_server_exceptions=True)
