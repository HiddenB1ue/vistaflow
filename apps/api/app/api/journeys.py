from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.dependencies import JourneyServiceDep
from app.schemas.common import APIResponse
from app.schemas.journey import JourneySearchRequest, JourneySearchResponse
from app.services.exceptions import BusinessError

router = APIRouter(prefix="/journeys", tags=["journeys"])


@router.post("/search", response_model=APIResponse[JourneySearchResponse])
async def search_journeys(
    payload: JourneySearchRequest,
    service: JourneyServiceDep,
) -> APIResponse[JourneySearchResponse]:
    try:
        result = await service.search(payload)
        return APIResponse.ok(result)
    except BusinessError as exc:
        return JSONResponse(  # type: ignore[return-value]
            status_code=exc.http_status,
            content=APIResponse.fail(exc.message).model_dump(),
        )
