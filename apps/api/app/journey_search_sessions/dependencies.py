from __future__ import annotations

import logging
from typing import Annotated, Protocol

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.integrations.ticket_12306.browser_manager import PlaywrightBrowserManager
from app.integrations.ticket_12306.client import build_ticket_client
from app.integrations.ticket_12306.service import Ticket12306Service
from app.journey_search_sessions.service import JourneySearchSessionService
from app.journeys.dependencies import JourneyServiceDep
from app.railway.dependencies import DbPool
from app.railway.repository import StationRepository
from app.route_plan_cache.repository import RoutePlanRepository
from app.system.settings_provider import SystemSettingsDataError

logger = logging.getLogger(__name__)

DEFAULT_TICKET_12306_CACHE_TTL_SECONDS = 600


class _IntSettingsProvider(Protocol):
    async def get_int(self, key: str) -> int: ...


def get_redis_client(request: Request) -> Redis:
    return request.app.state.redis_client  # type: ignore[no-any-return]


async def get_ticket_service(
    request: Request,
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    pool: DbPool,
) -> Ticket12306Service:
    browser_manager: PlaywrightBrowserManager = request.app.state.ticket_browser_manager
    settings_provider = request.app.state.system_settings_provider
    ticket_client = await build_ticket_client(
        settings_provider=settings_provider,
        browser_manager=browser_manager,
        redis_client=redis_client,
        cookie_pool=getattr(request.app.state, "cookie_pool", None),
    )
    cache_ttl_seconds = await _get_ticket_cache_ttl_seconds(settings_provider)
    return Ticket12306Service(
        redis_client=redis_client,
        station_repo=StationRepository(pool),
        ticket_client=ticket_client,
        cache_ttl_seconds=cache_ttl_seconds,
    )


async def _get_ticket_cache_ttl_seconds(settings_provider: _IntSettingsProvider) -> int:
    try:
        ttl_seconds = await settings_provider.get_int("ticket_12306_cache_ttl_seconds")
    except SystemSettingsDataError as exc:
        logger.warning("Failed to read ticket_12306_cache_ttl_seconds: %s", exc)
        return DEFAULT_TICKET_12306_CACHE_TTL_SECONDS
    return max(1, ttl_seconds)


def get_journey_search_session_service(
    journey_service: JourneyServiceDep,
    pool: DbPool,
    ticket_service: Annotated[Ticket12306Service, Depends(get_ticket_service)],
) -> JourneySearchSessionService:
    return JourneySearchSessionService(
        journey_service=journey_service,
        station_repo=StationRepository(pool),
        ticket_service=ticket_service,
        route_plan_repo=RoutePlanRepository(pool),
    )


JourneySearchSessionServiceDep = Annotated[
    JourneySearchSessionService,
    Depends(get_journey_search_session_service),
]
