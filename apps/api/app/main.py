from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.admin_data.router import router as admin_data_router
from app.auth.router import router as auth_router
from app.config import get_settings
from app.exceptions import BusinessError
from app.integrations.crawler.client import Live12306CrawlerClient
from app.integrations.geo.client import DynamicGeoClient
from app.integrations.ticket_12306.browser_manager import PlaywrightBrowserManager
from app.integrations.ticket_12306.cookie_pool import CookiePool
from app.journey_search_sessions.router import (
    router as journey_search_sessions_router,
)
from app.journeys.router import router as journeys_router
from app.railway.router import router as railway_router
from app.schemas import APIResponse
from app.system.dependencies import build_system_settings_provider
from app.system.router import health_router
from app.system.router import router as system_router
from app.tasks.registry import create_task_registry
from app.tasks.router import router as tasks_router

API_V1_PREFIX = "/api/v1"
ADMIN_API_V1_PREFIX = f"{API_V1_PREFIX}/admin"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    app.state.db_pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,
        max_size=20,
        command_timeout=30,
    )
    app.state.task_registry = create_task_registry()
    app.state.system_settings_provider = build_system_settings_provider(app.state.db_pool)
    app.state.ticket_browser_manager = PlaywrightBrowserManager()

    http_client = httpx.AsyncClient()
    app.state.http_client = http_client
    redis_client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    await redis_client.ping()
    app.state.redis_client = redis_client

    cookie_pool = CookiePool(
        redis_client=redis_client,
        browser_manager=app.state.ticket_browser_manager,
    )
    app.state.cookie_pool = cookie_pool

    app.state.crawler_client = Live12306CrawlerClient(http_client=http_client)
    app.state.geo_client = DynamicGeoClient(
        settings_provider=app.state.system_settings_provider,
        http_client=http_client,
    )

    refresh_task = asyncio.create_task(
        _cookie_pool_refresh_loop(cookie_pool)
    )

    yield

    refresh_task.cancel()
    await app.state.db_pool.close()
    await app.state.ticket_browser_manager.close()
    await http_client.aclose()
    await redis_client.aclose()


_COOKIE_POOL_REFRESH_INTERVAL_SECONDS = 20 * 60  # 20 minutes


logger = logging.getLogger(__name__)


async def _cookie_pool_refresh_loop(pool: CookiePool) -> None:
    """Periodically warm up empty cookie pool slots."""
    # Initial warmup on startup
    try:
        refreshed = await pool.refresh_pool()
        logger.info("Cookie pool initial warmup: %d slots refreshed", refreshed)
    except Exception as exc:
        logger.warning("Cookie pool initial warmup failed: %s", exc)

    while True:
        await asyncio.sleep(_COOKIE_POOL_REFRESH_INTERVAL_SECONDS)
        try:
            await pool.refresh_pool()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning("Cookie pool refresh failed: %s", exc)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="VistaFlow API",
        version=settings.app_version,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
        expose_headers=["Authorization"],
    )

    @app.exception_handler(BusinessError)
    async def business_error_handler(
        request: Request,
        exc: BusinessError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=APIResponse.fail(exc.message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=APIResponse.fail("服务器内部错误，请稍后重试").model_dump(),
        )

    app.include_router(railway_router, prefix=API_V1_PREFIX)
    app.include_router(journeys_router, prefix=API_V1_PREFIX)
    app.include_router(journey_search_sessions_router, prefix=API_V1_PREFIX)
    app.include_router(auth_router, prefix=API_V1_PREFIX)
    app.include_router(tasks_router, prefix=ADMIN_API_V1_PREFIX)
    app.include_router(health_router)
    app.include_router(admin_data_router, prefix=ADMIN_API_V1_PREFIX)
    app.include_router(system_router, prefix=ADMIN_API_V1_PREFIX)
    return app


app = create_app()
