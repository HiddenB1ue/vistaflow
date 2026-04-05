from __future__ import annotations

from fastapi import APIRouter

from app.schemas import APIResponse

from app.journeys.dependencies import JourneyServiceDep
from app.journeys.schemas import JourneySearchRequest, JourneySearchResponse

router = APIRouter(prefix="/journeys", tags=["journeys"])


@router.post("/search", response_model=APIResponse[JourneySearchResponse])
async def search_journeys(
    payload: JourneySearchRequest,
    service: JourneyServiceDep,
) -> APIResponse[JourneySearchResponse]:
    result = await service.search(payload)
    return APIResponse.ok(result)
