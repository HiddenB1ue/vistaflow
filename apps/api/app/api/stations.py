from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import StationServiceDep
from app.schemas.common import APIResponse
from app.schemas.station import StationGeoResponse, StationSuggestResponse

router = APIRouter(prefix="/stations", tags=["stations"])

StationNamesQuery = Annotated[list[str] | None, Query(description="站点名称列表")]
SuggestKeywordQuery = Annotated[
    str,
    Query(min_length=1, description="搜索关键词（站名/拼音/简拼）"),
]
SuggestLimitQuery = Annotated[int, Query(ge=1, le=30)]


@router.get("", response_model=APIResponse[StationGeoResponse])
async def get_stations_geo(
    service: StationServiceDep,
    names: StationNamesQuery = None,
) -> APIResponse[StationGeoResponse]:
    result = await service.get_geo(names or [])
    return APIResponse.ok(result)


@router.get("/suggest", response_model=APIResponse[StationSuggestResponse])
async def suggest_stations(
    q: SuggestKeywordQuery,
    service: StationServiceDep,
    limit: SuggestLimitQuery = 10,
) -> APIResponse[StationSuggestResponse]:
    result = await service.suggest(q.strip(), limit)
    return APIResponse.ok(result)
