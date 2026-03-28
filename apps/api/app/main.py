from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.config.settings import get_settings
from app.integrations.ticket_12306.client import (
    Live12306TicketClient,
    NullTicketClient,
    TicketClientConfig,
)
from app.schemas.common import APIResponse
from app.services.exceptions import BusinessError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    app.state.db_pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,
        max_size=20,
        command_timeout=30,
    )

    http_client = httpx.AsyncClient()
    app.state.http_client = http_client

    if settings.ticket_12306_cookie.strip():
        app.state.ticket_client = Live12306TicketClient(
            config=TicketClientConfig(
                endpoint=settings.ticket_12306_endpoint,
                cookie=settings.ticket_12306_cookie,
            ),
            http_client=http_client,
        )
    else:
        app.state.ticket_client = NullTicketClient()

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
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(BusinessError)
    async def business_error_handler(
        request: Request, exc: BusinessError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=APIResponse.fail(exc.message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=APIResponse.fail("服务器内部错误，请稍后重试").model_dump(),
        )

    app.include_router(router)

    return app


app = create_app()
