from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import require_admin_auth
from app.main import app
from app.tasks.dependencies import get_task_service
from app.tasks.schemas import (
    TaskMetrics,
    TaskParamResponse,
    TaskResponse,
    TaskRunLogResponse,
    TaskRunResponse,
    TaskTiming,
    TaskTypeResponse,
)

NOW = datetime(2026, 4, 5, tzinfo=UTC)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    mock_pool = MagicMock()
    mock_pool.close = AsyncMock()
    monkeypatch.setattr("app.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool))
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: SimpleNamespace(
            database_url="postgresql://test",
            ticket_12306_cookie="",
            amap_api_key="",
            app_env="test",
            app_version="test",
            cors_origins=["*"],
            task_worker_poll_interval_seconds=1.0,
            task_worker_heartbeat_interval_seconds=5.0,
            task_worker_stale_timeout_seconds=60.0,
        ),
    )
    app.dependency_overrides[require_admin_auth] = lambda: None
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def fake_service() -> MagicMock:
    service = MagicMock()
    service.list_task_types = AsyncMock(
        return_value=[
            TaskTypeResponse(
                type="fetch-trains",
                label="爬取车次",
                description="按日期和关键字抓取车次目录，并写入 trains 表。",
                implemented=True,
                supportsCron=True,
                paramSchema=[
                    TaskParamResponse(
                        key="date",
                        label="日期",
                        valueType="date",
                        required=True,
                        placeholder="2026-04-05",
                        description="支持 YYYY-MM-DD 或 YYYYMMDD，保存时统一为 YYYY-MM-DD。",
                    )
                ],
            )
        ]
    )
    service.list_tasks = AsyncMock(
        return_value=[
            TaskResponse(
                id=1,
                name="铁路任务",
                type="fetch-trains",
                typeLabel="爬取车次",
                status="idle",
                description="同步车次",
                enabled=True,
                cron=None,
                payload={"date": "2026-04-05", "keyword": "G"},
                metrics=TaskMetrics(label="最近结果", value=""),
                timing=TaskTiming(label="最近耗时", value=""),
                errorMessage=None,
                latestRun=None,
            )
        ]
    )
    service.get_task = AsyncMock(return_value=service.list_tasks.return_value[0])
    service.create_task = AsyncMock(return_value=service.list_tasks.return_value[0])
    service.update_task = AsyncMock(return_value=service.list_tasks.return_value[0])
    service.delete_task = AsyncMock(return_value=None)
    service.trigger_task = AsyncMock(
        return_value=TaskRunResponse(
            id=11,
            taskId=1,
            taskName="铁路任务",
            taskType="fetch-trains",
            triggerMode="manual",
            status="pending",
            requestedBy="admin",
            summary=None,
            resultLevel=None,
            metricsValue="",
            progressSnapshot={
                "version": 2,
                "taskType": "fetch-trains",
                "phase": "queued",
                "status": "pending",
                "summary": {
                    "totalUnits": 0,
                    "processedUnits": 0,
                    "successUnits": 0,
                    "failedUnits": 0,
                    "pendingUnits": 0,
                    "warningUnits": 0,
                },
                "current": {},
                "lastError": {},
                "details": {},
            },
            errorMessage=None,
            terminationReason=None,
            startedAt=None,
            finishedAt=None,
            createdAt=NOW,
            updatedAt=NOW,
        )
    )
    service.list_runs = AsyncMock(return_value=[service.trigger_task.return_value])
    service.get_run = AsyncMock(return_value=service.trigger_task.return_value)
    service.list_run_logs = AsyncMock(
        return_value=[
            TaskRunLogResponse(
                id=1,
                runId=11,
                severity="INFO",
                message="started",
                createdAt=NOW,
            )
        ]
    )
    service.terminate_run = AsyncMock(return_value=service.trigger_task.return_value)
    return service


def override_service(fake_service: MagicMock) -> None:
    app.dependency_overrides[get_task_service] = lambda: fake_service


def test_list_task_types(client: TestClient, fake_service: MagicMock) -> None:
    override_service(fake_service)
    response = client.get("/api/v1/admin/tasks/types")
    assert response.status_code == 200
    assert response.json()["data"][0]["type"] == "fetch-trains"
    assert response.json()["data"][0]["paramSchema"][0]["key"] == "date"


def test_create_task(client: TestClient, fake_service: MagicMock) -> None:
    override_service(fake_service)
    response = client.post(
        "/api/v1/admin/tasks",
        json={
            "name": "Train sync",
            "type": "fetch-trains",
            "payload": {"date": "2026-04-05", "keyword": "G"},
        },
    )
    assert response.status_code == 201
    fake_service.create_task.assert_awaited_once()


def test_update_task(client: TestClient, fake_service: MagicMock) -> None:
    override_service(fake_service)
    response = client.patch(
        "/api/v1/admin/tasks/1",
        json={"payload": {"date": "2026-04-06", "keyword": "D"}},
    )
    assert response.status_code == 200
    fake_service.update_task.assert_awaited_once()


def test_delete_task(client: TestClient, fake_service: MagicMock) -> None:
    override_service(fake_service)
    response = client.delete("/api/v1/admin/tasks/1")
    assert response.status_code == 204
    fake_service.delete_task.assert_awaited_once_with(1)


def test_trigger_task(client: TestClient, fake_service: MagicMock) -> None:
    override_service(fake_service)
    response = client.post("/api/v1/admin/tasks/1/runs")
    assert response.status_code == 202
    assert response.json()["data"]["taskId"] == 1
    assert response.json()["data"]["progressSnapshot"]["phase"] == "queued"


def test_list_task_runs(client: TestClient, fake_service: MagicMock) -> None:
    override_service(fake_service)
    response = client.get("/api/v1/admin/tasks/1/runs")
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == 11
    assert response.json()["data"][0]["progressSnapshot"]["status"] == "pending"


def test_get_task_run_logs(client: TestClient, fake_service: MagicMock) -> None:
    override_service(fake_service)
    response = client.get("/api/v1/admin/task-runs/11/logs")
    assert response.status_code == 200
    assert response.json()["data"][0]["message"] == "started"


def test_terminate_task_run(client: TestClient, fake_service: MagicMock) -> None:
    override_service(fake_service)
    response = client.post("/api/v1/admin/task-runs/11/terminate")
    assert response.status_code == 202
    fake_service.terminate_run.assert_awaited_once_with(11)
