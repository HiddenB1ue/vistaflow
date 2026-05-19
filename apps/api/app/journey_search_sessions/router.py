from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

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

logger = logging.getLogger(__name__)

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


@router.post("/stream")
async def create_search_session_stream(
    payload: SearchSessionCreateRequest,
    service: JourneySearchSessionServiceDep,
) -> StreamingResponse:
    """SSE endpoint that streams progress events during session creation.

    Each event is a JSON object on a ``data:`` line, terminated by ``\\n\\n``.
    Event types: ``phase``, ``plan_ready``, ``candidates_counted``,
    ``complete``, ``error``.
    """

    async def event_generator() -> AsyncIterator[str]:
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

        def on_progress(event: dict[str, Any]) -> None:
            queue.put_nowait(event)

        async def run_session() -> None:
            try:
                result = await service.create_session(
                    payload, on_progress=on_progress
                )
                queue.put_nowait({
                    "type": "complete",
                    "data": result.model_dump(mode="json"),
                })
            except Exception as exc:
                logger.warning("SSE session creation failed: %s", exc)
                queue.put_nowait({
                    "type": "error",
                    "message": str(exc),
                })
            finally:
                queue.put_nowait(None)

        task = asyncio.create_task(run_session())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


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


@router.post("/{search_id}/prices/stream")
async def stream_prices(
    search_id: str,
    service: JourneySearchSessionServiceDep,
) -> StreamingResponse:
    """SSE endpoint that streams ticket price results as they are fetched.

    Event types: ``pricing_started``, ``leg_priced``, ``pricing_complete``, ``error``.
    """

    async def event_generator() -> AsyncIterator[str]:
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

        def on_progress(event: dict[str, Any]) -> None:
            queue.put_nowait(event)

        def on_leg_complete(prices: dict[str, Any]) -> None:
            # Serialize PriceCacheEntry objects to dicts for JSON
            serialized = {}
            for k, v in prices.items():
                serialized[k] = v.model_dump(mode="json") if hasattr(v, "model_dump") else v
            queue.put_nowait({"type": "leg_priced", "prices": serialized})

        async def run_pricing() -> None:
            try:
                await service.stream_prices(
                    search_id.strip(),
                    on_leg_complete=on_leg_complete,
                    on_progress=on_progress,
                )
                queue.put_nowait({"type": "pricing_complete"})
            except Exception as exc:
                logger.warning("Price stream failed for %s: %s", search_id, exc)
                queue.put_nowait({"type": "error", "message": str(exc)})
            finally:
                queue.put_nowait(None)

        task = asyncio.create_task(run_pricing())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
