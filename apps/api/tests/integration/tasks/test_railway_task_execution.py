from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

from app.models import TaskDefinition
from app.tasks.handlers import (
    HandlerContext,
    build_train_run_rows,
    handle_fetch_train_runs,
    handle_fetch_train_stops,
    handle_fetch_trains,
)
from app.tasks.repository import TaskRunLogRepository, TaskRunRepository

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
        run_repo=AsyncMock(spec=TaskRunRepository),
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
    async def fake_fetch_trains(date: str, keyword: str) -> list[dict[str, Any]]:
        assert date == "2026-04-05"
        assert keyword == "G"
        return [
            {
                "train_no": "240000G1010A",
                "station_train_code": "G1",
                "from_station": "北京南",
                "to_station": "上海虹桥",
                "total_num": 2,
                "keyword": "G",
            }
        ]

    cast(Any, handler_context.crawler_client).fetch_trains = fake_fetch_trains

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool

        async def upsert_train_rows(self, rows: list[dict[str, object]]) -> int:
            return len(rows)

    monkeypatch.setattr("app.tasks.handlers.RailwayTaskRepository", FakeRepo)

    result = await handle_fetch_trains(handler_context)

    assert result.summary == "车次同步完成"
    assert result.metrics_value == "1"
    assert result.progress_snapshot is not None
    assert result.progress_snapshot["details"]["currentSeedKeyword"] == "G"
    assert result.progress_snapshot["details"]["uniqueTrainNosSeen"] == 1


@pytest.mark.asyncio
async def test_handle_fetch_trains_dispatches_roots_when_keyword_missing(
    handler_context: HandlerContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler_context.task = make_task("fetch-trains", {"date": "2026-04-05"})
    calls: list[str] = []

    async def fake_fetch_trains(date: str, keyword: str) -> list[dict[str, Any]]:
        assert date == "2026-04-05"
        calls.append(keyword)
        return [
            {
                "train_no": f"TN-{keyword.upper()}",
                "station_train_code": keyword.upper(),
                "from_station": "北京南",
                "to_station": "上海虹桥",
                "total_num": 2,
                "keyword": keyword,
            }
        ]

    cast(Any, handler_context.crawler_client).fetch_trains = fake_fetch_trains

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool

        async def upsert_train_rows(self, rows: list[dict[str, object]]) -> int:
            return len(rows)

    monkeypatch.setattr("app.tasks.handlers.RailwayTaskRepository", FakeRepo)
    monkeypatch.setattr("app.tasks.handlers.seed_keywords", lambda: ["g", "d"])

    result = await handle_fetch_trains(handler_context)

    assert calls == ["g", "d"]
    assert result.metrics_value == "2"
    assert result.progress_snapshot is not None
    assert result.progress_snapshot["details"]["completedSeedKeywords"] == 2
    assert result.progress_snapshot["summary"]["processedUnits"] == 2


@pytest.mark.asyncio
async def test_handle_fetch_train_stops_persists_stop_rows_only(
    handler_context: HandlerContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler_context.task = make_task(
        "fetch-train-stops",
        {"date": "2026-04-05", "keyword": "G1"},
    )
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
            self.stop_rows: list[dict[str, object]] = []

        async def find_train_nos_by_keyword(self, keyword: str) -> list[str]:
            assert keyword == "G1"
            return ["240000G1010A"]

        async def upsert_stop_rows(self, stop_rows: list[dict[str, object]]) -> int:
            self.stop_rows = stop_rows
            return len(stop_rows)

    fake_repo = FakeRepo(handler_context.pool)
    monkeypatch.setattr("app.tasks.handlers.RailwayTaskRepository", lambda pool: fake_repo)

    result = await handle_fetch_train_stops(handler_context)

    assert result.summary == "车次经停同步完成"
    assert result.metrics_value == "2"
    assert len(fake_repo.stop_rows) == 2


@pytest.mark.asyncio
async def test_handle_fetch_train_stops_uses_all_train_nos_when_keyword_missing(
    handler_context: HandlerContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler_context.task = make_task(
        "fetch-train-stops",
        {"date": "2026-04-05"},
    )

    async def fake_fetch_train_stops(train_no: str, date: str) -> list[dict[str, Any]]:
        assert date == "2026-04-05"
        return [
            {
                "train_no": train_no,
                "station_no": 1,
                "station_name": "北京南",
                "station_train_code": "G1",
                "start_station_name": "北京南",
                "end_station_name": "上海虹桥",
            }
        ]

    cast(Any, handler_context.crawler_client).fetch_train_stops = fake_fetch_train_stops

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool
            self.calls = 0

        async def list_all_train_nos(self) -> list[str]:
            return ["TN-1", "TN-2"]

        async def upsert_stop_rows(self, stop_rows: list[dict[str, object]]) -> int:
            self.calls += 1
            return len(stop_rows)

    fake_repo = FakeRepo(handler_context.pool)
    monkeypatch.setattr("app.tasks.handlers.RailwayTaskRepository", lambda pool: fake_repo)

    result = await handle_fetch_train_stops(handler_context)

    assert result.summary == "车次经停同步完成"
    assert result.metrics_value == "2"
    assert fake_repo.calls == 2


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
            "run_date": "2026-04-05",
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


def test_build_train_run_rows_filters_by_prefix_and_date() -> None:
    rows = build_train_run_rows(
        [
            {
                "train_no": "TN-G2",
                "station_train_code": "G2",
                "from_station": "北京南",
                "to_station": "上海虹桥",
                "total_num": 2,
                "run_date": "2026-04-05",
                "data_flag": "1",
            },
            {
                "train_no": "TN-G20",
                "station_train_code": "G20",
                "from_station": "北京南",
                "to_station": "上海虹桥",
                "total_num": 2,
                "date": "20260405",
                "data_flag": "0",
            },
            {
                "train_no": "TN-G219",
                "station_train_code": "G219",
                "from_station": "上海虹桥",
                "to_station": "张家界西",
                "total_num": 11,
                "run_date": "2026-04-05",
                "data_flag": None,
            },
            {
                "train_no": "TN-G3",
                "station_train_code": "G3",
                "from_station": "北京南",
                "to_station": "上海虹桥",
                "total_num": 2,
                "run_date": "2026-04-05",
                "data_flag": "1",
            },
            {
                "train_no": "TN-D2",
                "station_train_code": "D2",
                "from_station": "北京南",
                "to_station": "上海虹桥",
                "total_num": 2,
                "run_date": "2026-04-05",
                "data_flag": "1",
            },
            {
                "train_no": "TN-G21-OTHER-DATE",
                "station_train_code": "G21",
                "from_station": "北京南",
                "to_station": "上海虹桥",
                "total_num": 2,
                "run_date": "2026-04-06",
                "data_flag": "1",
            },
        ],
        run_date="2026-04-05",
        train_code="G2",
    )

    assert [row["station_train_code"] for row in rows] == ["G2", "G20", "G219"]
    assert [row["status"] for row in rows] == ["running", "suspended", "running"]


@pytest.mark.asyncio
async def test_handle_fetch_train_runs_filters_by_prefix_and_date(
    handler_context: HandlerContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler_context.task = make_task(
        "fetch-train-runs",
        {"date": "2026-04-05", "train_code": "G2"},
    )
    cast(Any, handler_context.crawler_client.fetch_train_runs).return_value = [
        {
            "train_no": "TN-G2",
            "station_train_code": "G2",
            "from_station": "北京南",
            "to_station": "上海虹桥",
            "total_num": 2,
            "run_date": "2026-04-05",
            "data_flag": "1",
        },
        {
            "train_no": "TN-G20",
            "station_train_code": "G20",
            "from_station": "北京南",
            "to_station": "上海虹桥",
            "total_num": 2,
            "date": "20260405",
            "data_flag": "0",
        },
        {
            "train_no": "TN-G219",
            "station_train_code": "G219",
            "from_station": "上海虹桥",
            "to_station": "张家界西",
            "total_num": 11,
            "run_date": "2026-04-05",
            "data_flag": None,
        },
        {
            "train_no": "TN-G3",
            "station_train_code": "G3",
            "from_station": "北京南",
            "to_station": "上海虹桥",
            "total_num": 2,
            "run_date": "2026-04-05",
            "data_flag": "1",
        },
        {
            "train_no": "TN-G21-OTHER-DATE",
            "station_train_code": "G21",
            "from_station": "北京南",
            "to_station": "上海虹桥",
            "total_num": 2,
            "run_date": "2026-04-06",
            "data_flag": "1",
        },
    ]

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool
            self.train_rows: list[dict[str, object]] = []
            self.run_rows: list[dict[str, object]] = []

        async def upsert_train_and_run_rows(
            self,
            train_rows: list[dict[str, object]],
            run_rows: list[dict[str, object]],
        ) -> tuple[int, int]:
            self.train_rows = train_rows
            self.run_rows = run_rows
            return len(train_rows), len(run_rows)

    fake_repo = FakeRepo(handler_context.pool)
    monkeypatch.setattr("app.tasks.handlers.RailwayTaskRepository", lambda pool: fake_repo)

    result = await handle_fetch_train_runs(handler_context)

    assert result.summary == "运行车次同步完成"
    assert result.metrics_value == "3"
    assert [row["station_train_code"] for row in fake_repo.run_rows] == ["G2", "G20", "G219"]
    assert all(row["run_date"] == "2026-04-05" for row in fake_repo.run_rows)
