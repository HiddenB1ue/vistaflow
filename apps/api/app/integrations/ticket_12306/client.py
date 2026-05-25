from __future__ import annotations

import asyncio
import inspect
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Any, cast

from app.integrations.ticket_12306.parser import LEFT_TICKET_QUERY_URL, parse_query_rows
from app.system.settings_provider import SystemSettingsDataError, SystemSettingsProvider

logger = logging.getLogger(__name__)

INIT_URL = "https://kyfw.12306.cn/otn/leftTicket/init"
REQUESTS_PER_WORKER_TARGET = 100
MAX_WORKERS = 10
REQUEST_RETRIES = 1
WORKER_TIMEOUT_SECONDS = 30
PAUSE_EVERY_REQUESTS = 10
PAUSE_SECONDS = 1.0

BASE_QUERY_PARAMS = {
    "purpose_codes": "ADULT",
}

SCRAPLING_HEADERS = {
    "Referer": INIT_URL,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


@dataclass(frozen=True)
class TicketLegRequest:
    run_date: str
    from_station: str
    to_station: str
    from_telecode: str
    to_telecode: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.run_date, self.from_station, self.to_station)


LegCompleteCallback = Callable[
    [TicketLegRequest, dict[str, Any]],
    Awaitable[None] | None,
]
SessionFactory = Callable[[], AbstractAsyncContextManager[Any]]


class AbstractTicketClient(ABC):
    """12306 ticket client contract for batch leg fetching."""

    @abstractmethod
    async def fetch_legs(
        self,
        legs: list[TicketLegRequest],
        *,
        on_leg_complete: LegCompleteCallback | None = None,
    ) -> dict[tuple[str, str, str], dict[str, Any]]:
        """Fetch leg-scoped query rows keyed by ``(date, from_station, to_station)``."""


class ScraplingTicketClient(AbstractTicketClient):
    """12306 ticket client using Scrapling sessions and queue-based workers."""

    def __init__(
        self,
        *,
        session_factory: SessionFactory | None = None,
        requests_per_worker_target: int = REQUESTS_PER_WORKER_TARGET,
        max_workers: int = MAX_WORKERS,
        pause_every_requests: int = PAUSE_EVERY_REQUESTS,
        pause_seconds: float = PAUSE_SECONDS,
    ) -> None:
        self._session_factory = session_factory or self._default_session_factory
        self._requests_per_worker_target = max(1, requests_per_worker_target)
        self._max_workers = max(1, max_workers)
        self._pause_every_requests = max(1, pause_every_requests)
        self._pause_seconds = max(0.0, pause_seconds)

    async def fetch_legs(
        self,
        legs: list[TicketLegRequest],
        *,
        on_leg_complete: LegCompleteCallback | None = None,
    ) -> dict[tuple[str, str, str], dict[str, Any]]:
        if not legs:
            return {}

        queue: asyncio.Queue[TicketLegRequest] = asyncio.Queue()
        for leg in legs:
            queue.put_nowait(leg)

        results: dict[tuple[str, str, str], dict[str, Any]] = {}
        worker_count = self.calculate_worker_count(
            len(legs),
            requests_per_worker_target=self._requests_per_worker_target,
            max_workers=self._max_workers,
        )

        async def worker(worker_id: int) -> None:
            processed = 0
            try:
                async with self._session_factory() as session:
                    init_page = await session.get(
                        INIT_URL,
                        headers=SCRAPLING_HEADERS,
                        follow_redirects=False,
                        timeout=WORKER_TIMEOUT_SECONDS,
                        retries=REQUEST_RETRIES,
                    )
                    cookies = _parse_set_cookie(
                        _header_get(getattr(init_page, "headers", {}), "set-cookie")
                    )
                    headers = _build_headers(cookies)

                    while True:
                        try:
                            leg = queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break

                        try:
                            rows = await self._fetch_one_leg(session, headers, leg)
                        except Exception as exc:  # noqa: BLE001 - per-leg failures degrade to empty rows
                            logger.warning(
                                "Scrapling ticket fetch failed for %s->%s on %s: %s",
                                leg.from_station,
                                leg.to_station,
                                leg.run_date,
                                exc,
                            )
                            rows = {}
                        finally:
                            queue.task_done()

                        results[leg.key] = rows
                        await _maybe_call(on_leg_complete, leg, rows)

                        processed += 1
                        if (
                            not queue.empty()
                            and processed % self._pause_every_requests == 0
                            and self._pause_seconds > 0
                        ):
                            await asyncio.sleep(self._pause_seconds)
            except Exception as exc:  # noqa: BLE001 - other workers may still complete the queue
                logger.warning("Scrapling ticket worker %d setup failed: %s", worker_id, exc)

        await asyncio.gather(*(worker(worker_id) for worker_id in range(worker_count)))

        for leg in legs:
            if leg.key in results:
                continue
            results[leg.key] = {}
            await _maybe_call(on_leg_complete, leg, {})

        return results

    async def _fetch_one_leg(
        self,
        session: Any,
        headers: dict[str, str],
        leg: TicketLegRequest,
    ) -> dict[str, Any]:
        page = await session.get(
            LEFT_TICKET_QUERY_URL,
            params={
                "leftTicketDTO.train_date": leg.run_date,
                "leftTicketDTO.from_station": leg.from_telecode,
                "leftTicketDTO.to_station": leg.to_telecode,
                **BASE_QUERY_PARAMS,
            },
            headers=headers,
            follow_redirects=False,
            timeout=WORKER_TIMEOUT_SECONDS,
            retries=REQUEST_RETRIES,
        )
        if getattr(page, "status", None) != 200:
            logger.info(
                "Scrapling ticket fetch returned status %s for %s->%s on %s",
                getattr(page, "status", None),
                leg.from_station,
                leg.to_station,
                leg.run_date,
            )
            return {}

        payload = await _response_json(page)
        return cast(dict[str, Any], parse_query_rows(payload))

    @staticmethod
    def calculate_worker_count(
        leg_count: int,
        *,
        requests_per_worker_target: int = REQUESTS_PER_WORKER_TARGET,
        max_workers: int = MAX_WORKERS,
    ) -> int:
        if leg_count <= 0:
            return 0
        target = max(1, requests_per_worker_target)
        cap = max(1, max_workers)
        return min(cap, max(1, (leg_count + target - 1) // target))

    @staticmethod
    def _default_session_factory() -> AbstractAsyncContextManager[Any]:
        from scrapling.fetchers import FetcherSession

        return cast(
            AbstractAsyncContextManager[Any],
            FetcherSession(
                impersonate="chrome",
                stealthy_headers=True,
                timeout=WORKER_TIMEOUT_SECONDS,
                retries=REQUEST_RETRIES,
            ),
        )


async def build_ticket_client(
    settings_provider: SystemSettingsProvider,
) -> AbstractTicketClient | None:
    """Build the production 12306 ticket client."""
    try:
        enabled = await settings_provider.get_bool("ticket_12306_enabled")
    except SystemSettingsDataError:
        return None

    if not enabled:
        return None
    return ScraplingTicketClient()


def _parse_set_cookie(set_cookie_header: str | None) -> dict[str, str]:
    cookie = SimpleCookie()
    cookie.load(set_cookie_header or "")
    return {key: morsel.value for key, morsel in cookie.items()}


def _build_cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in cookies.items())


def _build_headers(cookies: dict[str, str] | None = None) -> dict[str, str]:
    if not cookies:
        return dict(SCRAPLING_HEADERS)

    return {
        **SCRAPLING_HEADERS,
        "Cookie": _build_cookie_header(cookies),
        "Origin": "https://kyfw.12306.cn",
        "X-Requested-With": "XMLHttpRequest",
    }


def _header_get(headers: Any, name: str) -> str | None:
    value = headers.get(name) if hasattr(headers, "get") else None
    return str(value) if value is not None else None


async def _response_json(page: Any) -> Any:
    json_method = getattr(page, "json", None)
    if callable(json_method):
        payload = json_method()
        if inspect.isawaitable(payload):
            return await payload
        return payload

    text_value = getattr(page, "text", None)
    if callable(text_value):
        text = text_value()
        if inspect.isawaitable(text):
            text = await text
        return json.loads(str(text))
    if isinstance(text_value, str):
        return json.loads(text_value)

    content = getattr(page, "body", None)
    if isinstance(content, bytes):
        return json.loads(content.decode("utf-8"))
    if isinstance(content, str):
        return json.loads(content)
    return {}


async def _maybe_call(
    callback: LegCompleteCallback | None,
    leg: TicketLegRequest,
    rows: dict[str, Any],
) -> None:
    if callback is None:
        return
    result = callback(leg, rows)
    if result is not None:
        await result


__all__ = [
    "AbstractTicketClient",
    "LegCompleteCallback",
    "MAX_WORKERS",
    "REQUESTS_PER_WORKER_TARGET",
    "ScraplingTicketClient",
    "TicketLegRequest",
    "build_ticket_client",
]
