from __future__ import annotations

import asyncio
from datetime import datetime

from app.admin_data.repository import StationListFilters, TrainListFilters
from app.admin_data.schemas import StationGeoUpdateRequest
from app.admin_data.service import AdminDataService
from app.exceptions import BusinessError, NotFoundError


class FakeRepo:
    def __init__(self) -> None:
        self.last_station_filters: StationListFilters | None = None
        self.last_train_filters: TrainListFilters | None = None
        self.update_args: tuple[int, float | None, float | None, str] | None = None
        self.station_row: dict[str, object] | None = {
            "id": 1,
            "name": "上海",
            "telecode": "AOH",
            "pinyin": "shanghai",
            "abbr": "sh",
            "area_name": "上海",
            "country_name": "中国",
            "longitude": 121.3,
            "latitude": 31.1,
            "geo_source": "manual",
            "geo_updated_at": None,
            "updated_at": datetime(2026, 4, 9),
            "geo_status": "complete",
        }
        self.train_rows: list[dict[str, object]] = [
            {
                "id": 2,
                "train_no": "240000G1010A",
                "station_train_code": "G101",
                "from_station": "上海虹桥",
                "to_station": "北京南",
                "total_num": 8,
                "is_active": True,
                "updated_at": datetime(2026, 4, 9),
            }
        ]
        self.train_stop_rows: list[dict[str, object]] | None = [
            {
                "station_no": 1,
                "station_name": "上海虹桥",
                "station_train_code": "G101",
                "arrive_time": None,
                "start_time": "07:00",
                "running_time": None,
                "arrive_day_diff": 0,
                "arrive_day_str": "当日到达",
                "is_start": "Y",
                "start_station_name": "上海虹桥",
                "end_station_name": "北京南",
                "train_class_name": "高速",
                "service_type": "0",
                "wz_num": "--",
                "updated_at": datetime(2026, 4, 9),
            }
        ]

    async def list_stations(
        self,
        filters: StationListFilters,
    ) -> tuple[list[dict[str, object]], int]:
        self.last_station_filters = filters
        return ([self.station_row] if self.station_row else []), (1 if self.station_row else 0)

    async def update_station_geo(
        self,
        station_id: int,
        longitude: float | None,
        latitude: float | None,
        geo_source: str,
    ) -> dict[str, object] | None:
        self.update_args = (station_id, longitude, latitude, geo_source)
        return self.station_row

    async def list_trains(
        self,
        filters: TrainListFilters,
    ) -> tuple[list[dict[str, object]], int]:
        self.last_train_filters = filters
        return self.train_rows, len(self.train_rows)

    async def find_train_stops_by_train_id(
        self,
        train_id: int,
    ) -> list[dict[str, object]] | None:
        return self.train_stop_rows


def test_list_stations_builds_paginated_response() -> None:
    repo = FakeRepo()
    service = AdminDataService(repo=repo)  # type: ignore[arg-type]

    result = asyncio.run(
        service.list_stations(
            StationListFilters(
                page=2,
                page_size=10,
                keyword="sh",
                geo_status="missing",
                geo_source="manual",
                area_name="上海",
                sort_by="updatedAt",
                sort_order="desc",
            )
        )
    )

    assert result.page == 2
    assert result.pageSize == 10
    assert result.total == 1
    assert result.totalPages == 1
    assert result.items[0].telecode == "AOH"
    assert repo.last_station_filters is not None
    assert repo.last_station_filters.keyword == "sh"


def test_update_station_geo_rejects_half_empty_coordinates() -> None:
    repo = FakeRepo()
    service = AdminDataService(repo=repo)  # type: ignore[arg-type]

    try:
        asyncio.run(
            service.update_station_geo(
                1,
                StationGeoUpdateRequest(
                    longitude=121.3,
                    latitude=None,
                    geoSource="manual",
                ),
            )
        )
    except BusinessError as exc:
        assert "经纬度必须同时填写或同时清空" in exc.message
    else:
        raise AssertionError("Expected BusinessError")

def test_update_station_geo_rejects_invalid_range() -> None:
    repo = FakeRepo()
    service = AdminDataService(repo=repo)  # type: ignore[arg-type]

    try:
        asyncio.run(
            service.update_station_geo(
                1,
                StationGeoUpdateRequest(
                    longitude=181,
                    latitude=31.2,
                    geoSource="manual",
                ),
            )
        )
    except BusinessError as exc:
        assert "经度必须在 -180 到 180 之间" in exc.message
    else:
        raise AssertionError("Expected BusinessError")

def test_update_station_geo_returns_not_found() -> None:
    repo = FakeRepo()
    repo.station_row = None
    service = AdminDataService(repo=repo)  # type: ignore[arg-type]

    try:
        asyncio.run(
            service.update_station_geo(
                999,
                StationGeoUpdateRequest(
                    longitude=121.3,
                    latitude=31.2,
                    geoSource="manual",
                ),
            )
        )
    except NotFoundError as exc:
        assert "未找到站点" in exc.message
    else:
        raise AssertionError("Expected NotFoundError")

def test_list_train_stops_returns_empty_list_when_no_rows() -> None:
    repo = FakeRepo()
    repo.train_stop_rows = []
    service = AdminDataService(repo=repo)  # type: ignore[arg-type]

    result = asyncio.run(service.list_train_stops(1))

    assert result == []

def test_list_train_stops_raises_when_train_missing() -> None:
    repo = FakeRepo()
    repo.train_stop_rows = None
    service = AdminDataService(repo=repo)  # type: ignore[arg-type]

    try:
        asyncio.run(service.list_train_stops(404))
    except NotFoundError as exc:
        assert "未找到车次" in exc.message
    else:
        raise AssertionError("Expected NotFoundError")
