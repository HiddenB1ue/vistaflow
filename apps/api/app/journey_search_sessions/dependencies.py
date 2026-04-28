from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.config import get_settings
from app.integrations.ticket_12306.browser_manager import PlaywrightBrowserManager
from app.integrations.ticket_12306.client import build_ticket_client
from app.integrations.ticket_12306.service import Ticket12306Service
from app.journey_search_sessions.service import JourneySearchSessionService
from app.journeys.dependencies import JourneyServiceDep
from app.railway.dependencies import DbPool
from app.railway.repository import StationRepository


def get_redis_client(request: Request) -> Redis:
    return request.app.state.redis_client  # type: ignore[no-any-return]


async def get_ticket_service(
    request: Request,
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    pool: DbPool,
) -> Ticket12306Service:
    browser_manager: PlaywrightBrowserManager = request.app.state.ticket_browser_manager
    ticket_client = await build_ticket_client(
        settings_provider=request.app.state.system_settings_provider,
        browser_manager=browser_manager,
    )
    return Ticket12306Service(
        redis_client=redis_client,
        station_repo=StationRepository(pool),
        ticket_client=ticket_client,
    )


def get_journey_search_session_service(
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    journey_service: JourneyServiceDep,
    pool: DbPool,
    ticket_service: Annotated[Ticket12306Service, Depends(get_ticket_service)],
) -> JourneySearchSessionService:
    settings = get_settings()
    return JourneySearchSessionService(
        redis_client=redis_client,
        ttl_seconds=settings.journey_search_ttl_seconds,
        journey_service=journey_service,
        station_repo=StationRepository(pool),
        ticket_service=ticket_service,
    )


JourneySearchSessionServiceDep = Annotated[
    JourneySearchSessionService,
    Depends(get_journey_search_session_service),
]
