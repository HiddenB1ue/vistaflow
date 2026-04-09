from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.models import TaskDefinition
from app.tasks.exceptions import TaskExecutionError
from app.tasks.execution import TaskExecutionContext
from app.tasks.types.fetch_station_geo import execute_fetch_station_geo

NOW = datetime(2026, 4, 9, tzinfo=UTC)


def make_task(payload: dict[str, object]) -> TaskDefinition:
    return TaskDefinition(
        id=1,
        name="站点坐标补全",
        type="fetch-station-geo",
        type_label="站点坐标补全",
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
        latest_result_level=None,
        metrics_label="最近结果",
        metrics_value="",
        timing_label="最近耗时",
        timing_value="",
        error_message=None,
        created_at=NOW,
        updated_at=NOW,
    )


class FakeGeoClient:
    def __init__(
        self,
        responses: dict[str, tuple[float, float] | None] | None = None,
        *,
        configured: bool = True,
        errors: dict[str, Exception] | None = None,
    ) -> None:
        self.responses = responses or {}
        self.configured = configured
        self.errors = errors or {}
        self.calls: list[str] = []

    def is_configured(self) -> bool:
        return self.configured

    async def geocode_address(self, address: str) -> tuple[float, float] | None:
        self.calls.append(address)
        if address in self.errors:
            raise self.errors[address]
        return self.responses.get(address)


def make_context(payload: dict[str, object], geo_client: FakeGeoClient) -> TaskExecutionContext:
    return TaskExecutionContext(
        task=make_task(payload),
        run_id=11,
        pool=AsyncMock(),
        run_repo=AsyncMock(),
        run_log_repo=AsyncMock(),
        log_repo=AsyncMock(),
        crawler_client=AsyncMock(),
        geo_client=geo_client,
    )


@pytest.mark.asyncio
async def test_single_query_mode_returns_success_without_persisting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geo_client = FakeGeoClient({"上海虹桥站": (121.327512, 31.200759)})
    context = make_context({"address": "上海虹桥站"}, geo_client)

    class UnexpectedRepo:
        def __init__(self, pool: object) -> None:
            raise AssertionError("single query mode should not instantiate StationRepository")

    monkeypatch.setattr("app.tasks.types.fetch_station_geo.StationRepository", UnexpectedRepo)

    result = await execute_fetch_station_geo(context)

    assert result.summary == "地址坐标查询完成"
    assert result.result_level == "success"
    assert result.metrics_value == "1"
    assert geo_client.calls == ["上海虹桥站"]


@pytest.mark.asyncio
async def test_single_query_mode_returns_warning_when_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geo_client = FakeGeoClient({"未知站点": None})
    context = make_context({"address": "未知站点"}, geo_client)

    class UnexpectedRepo:
        def __init__(self, pool: object) -> None:
            raise AssertionError("single query mode should not instantiate StationRepository")

    monkeypatch.setattr("app.tasks.types.fetch_station_geo.StationRepository", UnexpectedRepo)

    result = await execute_fetch_station_geo(context)

    assert result.summary == "地址坐标查询完成，未找到匹配结果"
    assert result.result_level == "warning"
    assert result.metrics_value == "0"


@pytest.mark.asyncio
async def test_batch_mode_updates_missing_coordinates_and_appends_station_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geo_client = FakeGeoClient(
        {
            "上海虹桥站": (121.327512, 31.200759),
            "北京南站": None,
        }
    )
    context = make_context({}, geo_client)

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool
            self.updated: list[tuple[int, float, float, str]] = []

        async def find_geo_enrichment_candidates(self) -> list[dict[str, object]]:
            return [
                {"id": 1, "name": "上海虹桥", "longitude": None, "latitude": None},
                {"id": 2, "name": "北京南站", "longitude": None, "latitude": None},
            ]

        async def update_geo(
            self,
            station_id: int,
            longitude: float,
            latitude: float,
            geo_source: str,
        ) -> None:
            self.updated.append((station_id, longitude, latitude, geo_source))

    fake_repo = FakeRepo(context.pool)
    monkeypatch.setattr("app.tasks.types.fetch_station_geo.StationRepository", lambda pool: fake_repo)

    result = await execute_fetch_station_geo(context)

    assert result.summary == "站点坐标补全完成，部分站点查询失败"
    assert result.result_level == "warning"
    assert result.metrics_value == "1"
    assert geo_client.calls == ["上海虹桥站", "北京南站"]
    assert fake_repo.updated == [(1, 121.327512, 31.200759, "amap")]


@pytest.mark.asyncio
async def test_batch_mode_returns_success_when_no_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geo_client = FakeGeoClient({})
    context = make_context({}, geo_client)

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool

        async def find_geo_enrichment_candidates(self) -> list[dict[str, object]]:
            return []

    monkeypatch.setattr("app.tasks.types.fetch_station_geo.StationRepository", FakeRepo)

    result = await execute_fetch_station_geo(context)

    assert result.summary == "没有待补全坐标的站点"
    assert result.result_level == "success"
    assert result.metrics_value == "0"


@pytest.mark.asyncio
async def test_batch_mode_raises_when_all_candidates_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geo_client = FakeGeoClient({"上海虹桥站": None})
    context = make_context({}, geo_client)

    class FakeRepo:
        def __init__(self, pool: object) -> None:
            self.pool = pool

        async def find_geo_enrichment_candidates(self) -> list[dict[str, object]]:
            return [{"id": 1, "name": "上海虹桥", "longitude": None, "latitude": None}]

        async def update_geo(
            self,
            station_id: int,
            longitude: float,
            latitude: float,
            geo_source: str,
        ) -> None:
            raise AssertionError("all failed path should not persist coordinates")

    monkeypatch.setattr("app.tasks.types.fetch_station_geo.StationRepository", FakeRepo)

    with pytest.raises(TaskExecutionError):
        await execute_fetch_station_geo(context)


@pytest.mark.asyncio
async def test_task_fails_fast_when_geo_client_is_not_configured() -> None:
    geo_client = FakeGeoClient(configured=False)
    context = make_context({}, geo_client)

    with pytest.raises(TaskExecutionError):
        await execute_fetch_station_geo(context)
