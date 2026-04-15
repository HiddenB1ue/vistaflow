from __future__ import annotations

from fastapi import APIRouter

from app.journey_search_sessions.dependencies import JourneySearchSessionServiceDep
from app.journey_search_sessions.schemas import (
    SearchSessionCreateRequest,
    SearchSessionCreateResponse,
    SearchSessionDeleteResponse,
    SearchSessionSummaryResponse,
    SearchSessionViewRequest,
    SearchSessionViewResultResponse,
)
from app.schemas import APIResponse

router = APIRouter(
    prefix="/journey-search-sessions",
    tags=["journey-search-sessions"],
)


@router.post("", response_model=APIResponse[SearchSessionCreateResponse])
async def create_search_session(
    payload: SearchSessionCreateRequest,
    service: JourneySearchSessionServiceDep,
) -> APIResponse[SearchSessionCreateResponse]:
    return APIResponse.ok(await service.create_session(payload))


@router.get("/{search_id}", response_model=APIResponse[SearchSessionSummaryResponse])
async def get_search_session(
    search_id: str,
    service: JourneySearchSessionServiceDep,
) -> APIResponse[SearchSessionSummaryResponse]:
    return APIResponse.ok(await service.get_summary(search_id.strip()))


@router.post(
    "/{search_id}/view",
    response_model=APIResponse[SearchSessionViewResultResponse],
)
async def get_search_session_view(
    search_id: str,
    payload: SearchSessionViewRequest,
    service: JourneySearchSessionServiceDep,
) -> APIResponse[SearchSessionViewResultResponse]:
    return APIResponse.ok(await service.get_view(search_id.strip(), payload))


@router.delete(
    "/{search_id}",
    response_model=APIResponse[SearchSessionDeleteResponse],
)
async def delete_search_session(
    search_id: str,
    service: JourneySearchSessionServiceDep,
) -> APIResponse[SearchSessionDeleteResponse]:
    return APIResponse.ok(await service.delete_session(search_id.strip()))
