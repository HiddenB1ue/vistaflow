from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.admin_data.dependencies import AdminDataServiceDep
from app.admin_data.repository import StationListFilters, TrainListFilters
from app.admin_data.schemas import (
    GeoSourceFilter,
    GeoStatus,
    SortOrder,
    StationAdminItemResponse,
    StationAdminListResponse,
    StationGeoUpdateRequest,
    StationSortBy,
    TrainAdminListResponse,
    TrainIsActiveFilter,
    TrainSortBy,
    TrainStopAdminItemResponse,
)
from app.auth.dependencies import require_admin_auth
from app.schemas import APIResponse

router = APIRouter(
    prefix="/data",
    tags=["admin-data"],
    dependencies=[Depends(require_admin_auth)],
)

PageQuery = Annotated[int, Query(ge=1)]
PageSizeQuery = Annotated[int, Query(ge=1, le=100)]


@router.get(
    "/stations",
    response_model=APIResponse[StationAdminListResponse],
)
async def list_stations(
    service: AdminDataServiceDep,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
    keyword: Annotated[str | None, Query(alias="keyword")] = None,
    geo_status: Annotated[GeoStatus, Query(alias="geoStatus")] = "all",
    geo_source: Annotated[GeoSourceFilter, Query(alias="geoSource")] = "all",
    area_name: Annotated[str | None, Query(alias="areaName")] = None,
    sort_by: Annotated[StationSortBy, Query(alias="sortBy")] = "updatedAt",
    sort_order: Annotated[SortOrder, Query(alias="sortOrder")] = "desc",
) -> APIResponse[StationAdminListResponse]:
    result = await service.list_stations(
        StationListFilters(
            page=page,
            page_size=page_size,
            keyword=keyword.strip() if keyword and keyword.strip() else None,
            geo_status=geo_status,
            geo_source=geo_source,
            area_name=area_name.strip() if area_name and area_name.strip() else None,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )
    return APIResponse.ok(result)


@router.patch(
    "/stations/{station_id}/geo",
    response_model=APIResponse[StationAdminItemResponse],
)
async def update_station_geo(
    station_id: Annotated[int, Path(alias="station_id", ge=1)],
    payload: StationGeoUpdateRequest,
    service: AdminDataServiceDep,
) -> APIResponse[StationAdminItemResponse]:
    result = await service.update_station_geo(station_id, payload)
    return APIResponse.ok(result)


@router.get(
    "/trains",
    response_model=APIResponse[TrainAdminListResponse],
)
async def list_trains(
    service: AdminDataServiceDep,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
    keyword: Annotated[str | None, Query(alias="keyword")] = None,
    is_active: Annotated[TrainIsActiveFilter, Query(alias="isActive")] = "all",
    sort_by: Annotated[TrainSortBy, Query(alias="sortBy")] = "updatedAt",
    sort_order: Annotated[SortOrder, Query(alias="sortOrder")] = "desc",
) -> APIResponse[TrainAdminListResponse]:
    result = await service.list_trains(
        TrainListFilters(
            page=page,
            page_size=page_size,
            keyword=keyword.strip() if keyword and keyword.strip() else None,
            is_active=is_active,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )
    return APIResponse.ok(result)


@router.get(
    "/trains/{train_id}/stops",
    response_model=APIResponse[list[TrainStopAdminItemResponse]],
)
async def list_train_stops(
    train_id: Annotated[int, Path(alias="train_id", ge=1)],
    service: AdminDataServiceDep,
) -> APIResponse[list[TrainStopAdminItemResponse]]:
    result = await service.list_train_stops(train_id)
    return APIResponse.ok(result)
