from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

from app.models import TaskDefinition
from app.tasks.handlers import (
    HandlerContext,
    handle_fetch_train_runs,
    handle_fetch_train_stops,
    handle_fetch_trains,
)
from app.tasks.repository import TaskRunLogRepository

NOW = datetime(2026, 4, 6, tzinfo=UTC)


def make_task(task_type: str, payload: dict[str, object]) -> TaskDefinition:
    return TaskDefinition(
        id=1,
        name="铁路任务",
        type=task_type,
        type_label=task_type,
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


@pytest.fixture
def handler_context() -> HandlerContext:
    return HandlerContext(
        task=make_task("fetch-trains", {"date": "2026-04-05", "keyword": "G"}),
        run_id=99,
        pool=AsyncMock(),
        run_log_repo=AsyncMock(spec=TaskRunLogRepository),
        log_repo=AsyncMock(),
        crawler_client=AsyncMock(),
        geo_client=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_handle_fetch_trains_writes_summary(
    handler_context: HandlerContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cast(Any, handler_context.crawler_client.fetch_trains).return_value = [
        {
            "train_no": "240000G1010A",
            "station_train_code": "G1",
            "from_station": "北京南",
            "to_station": "上海虹桥",
            "total_num": 2,
        }
    ]

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool

        async def upsert_train_rows(self, rows: list[dict[str, object]]) -> int:
            return len(rows)

    monkeypatch.setattr("app.tasks.handlers.RailwayTaskRepository", FakeRepo)

    result = await handle_fetch_trains(handler_context)

    assert result.summary == "车次同步完成"
    assert result.metrics_value == "1"


@pytest.mark.asyncio
async def test_handle_fetch_train_stops_persists_parent_train_and_stops(
    handler_context: HandlerContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler_context.task = make_task(
        "fetch-train-stops",
        {"date": "2026-04-05", "train_code": "G1"},
    )
    cast(Any, handler_context.crawler_client.fetch_trains).return_value = [
        {
            "train_no": "240000G1010A",
            "station_train_code": "G1",
            "from_station": "北京南",
            "to_station": "上海虹桥",
            "total_num": 2,
        }
    ]
    cast(Any, handler_context.crawler_client.fetch_train_stops).return_value = [
        {
            "train_no": "240000G1010A",
            "station_no": 1,
            "station_name": "北京南",
            "station_train_code": "G1",
            "start_station_name": "北京南",
            "end_station_name": "上海虹桥",
        },
        {
            "train_no": "240000G1010A",
            "station_no": 2,
            "station_name": "上海虹桥",
            "station_train_code": "G1",
            "start_station_name": "北京南",
            "end_station_name": "上海虹桥",
        },
    ]

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool

        async def upsert_train_and_stop_rows(
            self,
            train_rows: list[dict[str, object]],
            stop_rows: list[dict[str, object]],
        ) -> tuple[int, int]:
            return len(train_rows), len(stop_rows)

    monkeypatch.setattr("app.tasks.handlers.RailwayTaskRepository", FakeRepo)

    result = await handle_fetch_train_stops(handler_context)

    assert result.summary == "车次经停同步完成"
    assert result.metrics_value == "2"


@pytest.mark.asyncio
async def test_handle_fetch_train_runs_persists_run_facts(
    handler_context: HandlerContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler_context.task = make_task(
        "fetch-train-runs",
        {"date": "2026-04-05", "train_code": "G1"},
    )
    cast(Any, handler_context.crawler_client.fetch_train_runs).return_value = [
        {
            "train_no": "240000G1010A",
            "station_train_code": "G1",
            "from_station": "北京南",
            "to_station": "上海虹桥",
            "total_num": 2,
            "data_flag": "1",
        }
    ]

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool

        async def upsert_train_and_run_rows(
            self,
            train_rows: list[dict[str, object]],
            run_rows: list[dict[str, object]],
        ) -> tuple[int, int]:
            return len(train_rows), len(run_rows)

    monkeypatch.setattr("app.tasks.handlers.RailwayTaskRepository", FakeRepo)

    result = await handle_fetch_train_runs(handler_context)

    assert result.summary == "运行车次同步完成"
    assert result.metrics_value == "1"
