from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.config import get_settings
from app.journey_search_sessions.service import JourneySearchSessionService
from app.journeys.dependencies import JourneyServiceDep
from app.railway.dependencies import DbPool
from app.railway.repository import StationRepository


def get_redis_client(request: Request) -> Redis:
    return request.app.state.redis_client  # type: ignore[no-any-return]


def get_journey_search_session_service(
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    journey_service: JourneyServiceDep,
    pool: DbPool,
) -> JourneySearchSessionService:
    settings = get_settings()
    return JourneySearchSessionService(
        redis_client=redis_client,
        ttl_seconds=settings.journey_search_ttl_seconds,
        journey_service=journey_service,
        station_repo=StationRepository(pool),
    )


JourneySearchSessionServiceDep = Annotated[
    JourneySearchSessionService,
    Depends(get_journey_search_session_service),
]
