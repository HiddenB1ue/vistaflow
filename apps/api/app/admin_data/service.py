from __future__ import annotations

from app.admin_data.repository import (
    AdminDataRepository,
    StationListFilters,
    TrainListFilters,
    calc_total_pages,
)
from app.admin_data.schemas import (
    StationAdminItemResponse,
    StationAdminListResponse,
    StationGeoUpdateRequest,
    TrainAdminItemResponse,
    TrainAdminListResponse,
    TrainStopAdminItemResponse,
)
from app.exceptions import BusinessError, NotFoundError


def _map_station_item(row: dict[str, object]) -> StationAdminItemResponse:
    return StationAdminItemResponse(
        id=int(row["id"]),
        name=str(row["name"]),
        telecode=str(row["telecode"]),
        pinyin=str(row["pinyin"]) if row.get("pinyin") is not None else None,
        abbr=str(row["abbr"]) if row.get("abbr") is not None else None,
        areaName=str(row["area_name"]) if row.get("area_name") is not None else None,
        countryName=(
            str(row["country_name"]) if row.get("country_name") is not None else None
        ),
        longitude=(
            float(row["longitude"]) if row.get("longitude") is not None else None
        ),
        latitude=float(row["latitude"]) if row.get("latitude") is not None else None,
        geoSource=str(row["geo_source"]) if row.get("geo_source") is not None else None,
        geoUpdatedAt=row.get("geo_updated_at"),
        updatedAt=row["updated_at"],
        geoStatus=str(row["geo_status"]),
    )


def _map_train_item(row: dict[str, object]) -> TrainAdminItemResponse:
    return TrainAdminItemResponse(
        id=int(row["id"]),
        trainNo=str(row["train_no"]),
        stationTrainCode=(
            str(row["station_train_code"])
            if row.get("station_train_code") is not None
            else None
        ),
        fromStation=str(row["from_station"]) if row.get("from_station") is not None else None,
        toStation=str(row["to_station"]) if row.get("to_station") is not None else None,
        totalNum=int(row["total_num"]) if row.get("total_num") is not None else None,
        isActive=bool(row["is_active"]),
        updatedAt=row["updated_at"],
    )


def _map_train_stop_item(row: dict[str, object]) -> TrainStopAdminItemResponse:
    return TrainStopAdminItemResponse(
        stationNo=int(row["station_no"]),
        stationName=str(row["station_name"]) if row.get("station_name") is not None else None,
        stationTrainCode=(
            str(row["station_train_code"])
            if row.get("station_train_code") is not None
            else None
        ),
        arriveTime=str(row["arrive_time"]) if row.get("arrive_time") is not None else None,
        startTime=str(row["start_time"]) if row.get("start_time") is not None else None,
        runningTime=(
            str(row["running_time"]) if row.get("running_time") is not None else None
        ),
        arriveDayDiff=(
            int(row["arrive_day_diff"])
            if row.get("arrive_day_diff") is not None
            else None
        ),
        arriveDayStr=(
            str(row["arrive_day_str"]) if row.get("arrive_day_str") is not None else None
        ),
        isStart=str(row["is_start"]) if row.get("is_start") is not None else None,
        startStationName=(
            str(row["start_station_name"])
            if row.get("start_station_name") is not None
            else None
        ),
        endStationName=(
            str(row["end_station_name"])
            if row.get("end_station_name") is not None
            else None
        ),
        trainClassName=(
            str(row["train_class_name"])
            if row.get("train_class_name") is not None
            else None
        ),
        serviceType=(
            str(row["service_type"]) if row.get("service_type") is not None else None
        ),
        wzNum=str(row["wz_num"]) if row.get("wz_num") is not None else None,
        updatedAt=row["updated_at"],
    )


class AdminDataService:
    def __init__(self, repo: AdminDataRepository) -> None:
        self._repo = repo

    async def list_stations(self, filters: StationListFilters) -> StationAdminListResponse:
        rows, total = await self._repo.list_stations(filters)
        return StationAdminListResponse(
            items=[_map_station_item(row) for row in rows],
            page=filters.page,
            pageSize=filters.page_size,
            total=total,
            totalPages=calc_total_pages(total, filters.page_size),
        )

    async def update_station_geo(
        self,
        station_id: int,
        payload: StationGeoUpdateRequest,
    ) -> StationAdminItemResponse:
        _validate_station_geo_payload(payload)
        row = await self._repo.update_station_geo(
            station_id=station_id,
            longitude=payload.longitude,
            latitude=payload.latitude,
            geo_source=payload.geoSource,
        )
        if row is None:
            raise NotFoundError("未找到站点")
        return _map_station_item(row)

    async def list_trains(self, filters: TrainListFilters) -> TrainAdminListResponse:
        rows, total = await self._repo.list_trains(filters)
        return TrainAdminListResponse(
            items=[_map_train_item(row) for row in rows],
            page=filters.page,
            pageSize=filters.page_size,
            total=total,
            totalPages=calc_total_pages(total, filters.page_size),
        )

    async def list_train_stops(self, train_id: int) -> list[TrainStopAdminItemResponse]:
        rows = await self._repo.find_train_stops_by_train_id(train_id)
        if rows is None:
            raise NotFoundError("未找到车次")
        return [_map_train_stop_item(row) for row in rows]


def _validate_station_geo_payload(payload: StationGeoUpdateRequest) -> None:
    has_longitude = payload.longitude is not None
    has_latitude = payload.latitude is not None
    if has_longitude != has_latitude:
        raise BusinessError("经纬度必须同时填写或同时清空")

    if payload.longitude is None and payload.latitude is None:
        return

    assert payload.longitude is not None
    assert payload.latitude is not None
    if not -180 <= payload.longitude <= 180:
        raise BusinessError("经度必须在 -180 到 180 之间")
    if not -90 <= payload.latitude <= 90:
        raise BusinessError("纬度必须在 -90 到 90 之间")
