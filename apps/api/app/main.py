from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.admin_data.router import router as admin_data_router
from app.config import get_settings
from app.exceptions import BusinessError
from app.integrations.crawler.client import Live12306CrawlerClient
from app.integrations.geo.client import DynamicGeoClient
from app.integrations.ticket_12306.client import (
    DynamicTicketClient,
)
from app.journeys.router import router as journeys_router
from app.railway.router import router as railway_router
from app.schemas import APIResponse
from app.system.dependencies import build_system_settings_provider
from app.system.router import health_router, router as system_router
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

    http_client = httpx.AsyncClient()
    app.state.http_client = http_client

    app.state.ticket_client = DynamicTicketClient(
        settings_provider=app.state.system_settings_provider,
        http_client=http_client,
    )
    app.state.crawler_client = Live12306CrawlerClient(http_client=http_client)
    app.state.geo_client = DynamicGeoClient(
        settings_provider=app.state.system_settings_provider,
        http_client=http_client,
    )

    yield

    await app.state.db_pool.close()
    await http_client.aclose()


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
    app.include_router(tasks_router, prefix=ADMIN_API_V1_PREFIX)
    app.include_router(health_router)
    app.include_router(admin_data_router, prefix=ADMIN_API_V1_PREFIX)
    app.include_router(system_router, prefix=ADMIN_API_V1_PREFIX)
    return app


app = create_app()
