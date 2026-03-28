from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.dependencies import TrainServiceDep
from app.schemas.common import APIResponse
from app.schemas.train import TrainStopsResponse
from app.services.exceptions import BusinessError

router = APIRouter(prefix="/trains", tags=["trains"])

FromStationQuery = Annotated[str, Query(min_length=1, description="起始站名")]
ToStationQuery = Annotated[str, Query(min_length=1, description="终到站名")]
FullRouteQuery = Annotated[bool, Query(description="是否返回全程经停")]


@router.get("/{train_code}/stops", response_model=APIResponse[TrainStopsResponse])
async def get_train_stops(
    train_code: str,
    from_station: FromStationQuery,
    to_station: ToStationQuery,
    service: TrainServiceDep,
    full_route: FullRouteQuery = False,
) -> APIResponse[TrainStopsResponse]:
    try:
        result = await service.get_stops(
            train_code=train_code.strip(),
            from_station=from_station.strip(),
            to_station=to_station.strip(),
            full_route=full_route,
        )
        return APIResponse.ok(result)
    except BusinessError as exc:
        return JSONResponse(  # type: ignore[return-value]
            status_code=exc.http_status,
            content=APIResponse.fail(exc.message).model_dump(),
        )
