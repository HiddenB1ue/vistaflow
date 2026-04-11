from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.railway.dependencies import StationServiceDep, TrainServiceDep
from app.railway.schemas import (
    StationFullResponse,
    StationSuggestResponse,
    TrainStopsResponse,
)
from app.schemas import APIResponse

router = APIRouter(tags=["railway"])

# ---------------------------------------------------------------------------
# Station query-type aliases
# ---------------------------------------------------------------------------

StationNamesQuery = Annotated[list[str] | None, Query(description="站点名称列表")]
SuggestKeywordQuery = Annotated[
    str,
    Query(min_length=1, description="搜索关键词（站名/拼音/简拼）"),
]
SuggestLimitQuery = Annotated[int, Query(ge=1, le=30)]

# ---------------------------------------------------------------------------
# Train query-type aliases
# ---------------------------------------------------------------------------

FromStationQuery = Annotated[str, Query(min_length=1, description="起始站名")]
ToStationQuery = Annotated[str, Query(min_length=1, description="终到站名")]
FullRouteQuery = Annotated[bool, Query(description="是否返回全程经停")]

# ---------------------------------------------------------------------------
# Station routes
# ---------------------------------------------------------------------------


@router.get("/stations", response_model=APIResponse[list[StationFullResponse]])
async def get_stations(
    service: StationServiceDep,
    names: StationNamesQuery = None,
) -> APIResponse[list[StationFullResponse]]:
    result = await service.list_stations(names)
    return APIResponse.ok(result)


@router.get("/stations/all", response_model=APIResponse[StationSuggestResponse])
async def get_all_stations(
    service: StationServiceDep,
) -> APIResponse[StationSuggestResponse]:
    """返回所有车站的简化信息，用于前端缓存"""
    result = await service.get_all_for_cache()
    return APIResponse.ok(result)


@router.get("/stations/suggest", response_model=APIResponse[StationSuggestResponse])
async def suggest_stations(
    q: SuggestKeywordQuery,
    service: StationServiceDep,
    limit: SuggestLimitQuery = 10,
) -> APIResponse[StationSuggestResponse]:
    result = await service.suggest(q.strip(), limit)
    return APIResponse.ok(result)


# ---------------------------------------------------------------------------
# Train routes
# ---------------------------------------------------------------------------


@router.get("/trains/{train_code}/stops", response_model=APIResponse[TrainStopsResponse])
async def get_train_stops(
    train_code: str,
    from_station: FromStationQuery,
    to_station: ToStationQuery,
    service: TrainServiceDep,
    full_route: FullRouteQuery = False,
) -> APIResponse[TrainStopsResponse]:
    result = await service.get_stops(
        train_code=train_code.strip(),
        from_station=from_station.strip(),
        to_station=to_station.strip(),
        full_route=full_route,
    )
    return APIResponse.ok(result)
