from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import require_admin_auth
from app.main import app
from app.models import TaskDefinition
from app.tasks.dependencies import get_task_service
from app.tasks.repository import TaskRepository, TaskRunLogRepository, TaskRunRepository
from app.tasks.runner import TaskRunner
from app.tasks.service import TaskService

NOW = datetime(2026, 4, 6, tzinfo=UTC)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    mock_pool = MagicMock()
    mock_pool.close = AsyncMock()
    monkeypatch.setattr("app.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool))
    monkeypatch.setattr("app.main.TaskRunRepository.recover_incomplete_runs", AsyncMock())
    monkeypatch.setattr("app.main.TaskRepository.recover_incomplete_tasks", AsyncMock())
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: SimpleNamespace(
            database_url="postgresql://test",
            ticket_12306_cookie="",
            ticket_12306_endpoint="queryG",
            amap_api_key="",
            app_env="test",
            app_version="test",
            cors_origins=["*"],
        ),
    )
    app.dependency_overrides[require_admin_auth] = lambda: None
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def service_bundle() -> tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock]:
    task_repo = AsyncMock(spec=TaskRepository)
    run_repo = AsyncMock(spec=TaskRunRepository)
    run_log_repo = AsyncMock(spec=TaskRunLogRepository)
    runner = MagicMock(spec=TaskRunner)
    runner.schedule = MagicMock()
    runner.terminate = AsyncMock()
    service = TaskService(
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        runner=runner,
    )
    return service, task_repo, run_repo, run_log_repo, runner


def _make_task(task_type: str, payload: dict[str, object]) -> TaskDefinition:
    return TaskDefinition(
        id=1,
        name="铁路任务",
        type=task_type,
        type_label="铁路任务",
        description="test",
        enabled=True,
        cron=None,
        payload=payload,
        status="idle",
        latest_run_id=None,
        latest_run_status=None,
        latest_run_started_at=None,
        latest_run_finished_at=None,
        latest_error_message=None,
        metrics_label="最近结果",
        metrics_value="",
        timing_label="最近耗时",
        timing_value="",
        error_message=None,
        created_at=NOW,
        updated_at=NOW,
    )


def test_create_railway_task_normalizes_payload(
    client: TestClient,
    service_bundle: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    service, task_repo, _, _, _ = service_bundle
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = _make_task(
        "fetch-trains",
        {"date": "2026-04-05", "keyword": "G"},
    )
    app.dependency_overrides[get_task_service] = lambda: service

    response = client.post(
        "/tasks",
        json={
            "name": "Train sync",
            "type": "fetch-trains",
            "enabled": True,
            "payload": {"date": "20260405", "keyword": " G "},
        },
    )

    assert response.status_code == 201
    task_repo.create_task.assert_awaited_once()
    assert task_repo.create_task.await_args.kwargs["payload"] == {
        "date": "2026-04-05",
        "keyword": "G",
    }


def test_create_railway_task_rejects_invalid_payload(
    client: TestClient,
    service_bundle: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    service, task_repo, _, _, _ = service_bundle
    task_repo.find_by_name.return_value = None
    app.dependency_overrides[get_task_service] = lambda: service

    response = client.post(
        "/tasks",
        json={
            "name": "Broken task",
            "type": "fetch-train-stops",
            "enabled": True,
            "payload": {"date": "bad-date", "train_code": " "},
        },
    )

    assert response.status_code == 400
    assert "参数无效" in response.json()["error"]
