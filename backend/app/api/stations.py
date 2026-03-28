from __future__ import annotations

from fastapi import APIRouter, Query

from app.dependencies import StationServiceDep
from app.schemas.common import APIResponse
from app.schemas.station import StationGeoResponse, StationSuggestResponse

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("", response_model=APIResponse[StationGeoResponse])
async def get_stations_geo(
    names: list[str] = Query(default_factory=list, description="站点名称列表"),
    service: StationServiceDep = ...,
) -> APIResponse[StationGeoResponse]:
    result = await service.get_geo(names)
    return APIResponse.ok(result)


@router.get("/suggest", response_model=APIResponse[StationSuggestResponse])
async def suggest_stations(
    q: str = Query(min_length=1, description="搜索关键词（站名/拼音/简拼）"),
    limit: int = Query(default=10, ge=1, le=30),
    service: StationServiceDep = ...,
) -> APIResponse[StationSuggestResponse]:
    result = await service.suggest(q.strip(), limit)
    return APIResponse.ok(result)
