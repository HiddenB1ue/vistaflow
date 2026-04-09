from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from app.admin_data.repository import StationListFilters, TrainListFilters
from app.admin_data.router import (
    list_stations,
    list_train_stops,
    list_trains,
    update_station_geo,
)
from app.admin_data.schemas import (
    StationAdminItemResponse,
    StationAdminListResponse,
    StationGeoUpdateRequest,
    TrainAdminItemResponse,
    TrainAdminListResponse,
    TrainStopAdminItemResponse,
)

NOW = datetime(2026, 4, 9, tzinfo=UTC)


def make_service() -> MagicMock:
    service = MagicMock()
    service.list_stations = AsyncMock(
        return_value=StationAdminListResponse(
            items=[
                StationAdminItemResponse(
                    id=1,
                    name="上海",
                    telecode="AOH",
                    pinyin="shanghai",
                    abbr="sh",
                    areaName="上海",
                    countryName="中国",
                    longitude=None,
                    latitude=None,
                    geoSource=None,
                    geoUpdatedAt=None,
                    updatedAt=NOW,
                    geoStatus="missing",
                )
            ],
            page=1,
            pageSize=20,
            total=1,
            totalPages=1,
        )
    )
    service.update_station_geo = AsyncMock(
        return_value=StationAdminItemResponse(
            id=1,
            name="上海",
            telecode="AOH",
            pinyin="shanghai",
            abbr="sh",
            areaName="上海",
            countryName="中国",
            longitude=121.3,
            latitude=31.2,
            geoSource="manual",
            geoUpdatedAt=NOW,
            updatedAt=NOW,
            geoStatus="complete",
        )
    )
    service.list_trains = AsyncMock(
        return_value=TrainAdminListResponse(
            items=[
                TrainAdminItemResponse(
                    id=2,
                    trainNo="240000G1010A",
                    stationTrainCode="G101",
                    fromStation="上海虹桥",
                    toStation="北京南",
                    totalNum=8,
                    isActive=True,
                    updatedAt=NOW,
                )
            ],
            page=1,
            pageSize=20,
            total=1,
            totalPages=1,
        )
    )
    service.list_train_stops = AsyncMock(
        return_value=[
            TrainStopAdminItemResponse(
                stationNo=1,
                stationName="上海虹桥",
                stationTrainCode="G101",
                arriveTime=None,
                startTime="07:00",
                runningTime=None,
                arriveDayDiff=0,
                arriveDayStr="当日到达",
                isStart="Y",
                startStationName="上海虹桥",
                endStationName="北京南",
                trainClassName="高速",
                serviceType="0",
                wzNum="--",
                updatedAt=NOW,
            )
        ]
    )
    return service


def test_list_stations_uses_admin_data_service() -> None:
    service = make_service()

    response = asyncio.run(
        list_stations(
            service,
            page=2,
            page_size=50,
            keyword="AOH",
            geo_status="missing",
            geo_source="manual",
            area_name="上海",
            sort_by="updatedAt",
            sort_order="desc",
        )
    )

    assert response.data is not None
    assert response.data.items[0].telecode == "AOH"
    filters = service.list_stations.await_args.args[0]
    assert isinstance(filters, StationListFilters)
    assert filters.page == 2
    assert filters.geo_status == "missing"


def test_update_station_geo_uses_admin_data_service() -> None:
    service = make_service()

    response = asyncio.run(
        update_station_geo(
            1,
            StationGeoUpdateRequest(
                longitude=121.3,
                latitude=31.2,
                geoSource="manual",
            ),
            service,
        )
    )

    assert response.data is not None
    assert response.data.geoStatus == "complete"
    service.update_station_geo.assert_awaited_once()


def test_list_trains_uses_admin_data_service() -> None:
    service = make_service()

    response = asyncio.run(
        list_trains(
            service,
            page=1,
            page_size=20,
            keyword="G101",
            is_active="true",
            sort_by="updatedAt",
            sort_order="desc",
        )
    )

    assert response.data is not None
    assert response.data.items[0].trainNo == "240000G1010A"
    filters = service.list_trains.await_args.args[0]
    assert isinstance(filters, TrainListFilters)
    assert filters.is_active == "true"


def test_list_train_stops_uses_admin_data_service() -> None:
    service = make_service()

    response = asyncio.run(list_train_stops(2, service))

    assert response.data is not None
    assert response.data[0].stationNo == 1
    service.list_train_stops.assert_awaited_once_with(2)
