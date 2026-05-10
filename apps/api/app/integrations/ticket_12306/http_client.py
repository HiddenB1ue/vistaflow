from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx

from app.integrations.ticket_12306.client import AbstractTicketClient
from app.integrations.ticket_12306.cookie_manager import Ticket12306CookieManager
from app.integrations.ticket_12306.models import TicketSegmentData
from app.integrations.ticket_12306.parser import (
    BASE_HEADERS,
    LEFT_TICKET_QUERY_URL,
    build_seat_infos,
    parse_query_rows,
    segment_min_price,
)
from app.models import SeatLookupKey

logger = logging.getLogger(__name__)


class TicketHttpFailure(Exception):
    """HTTP path failed in a way that should trigger Playwright fallback."""


class HttpTicketClient(AbstractTicketClient):
    """12306 ticket client that talks to ``leftTicket/queryG`` over HTTP.

    Uses cookies from :class:`Ticket12306CookieManager`. On failure signals
    such as ``status=false``, redirects, or 5xx responses, performs a single
    in-place retry after refreshing cookies. If retry still fails, raises
    :class:`TicketHttpFailure` so the fallback layer can switch to Playwright.
    """

    def __init__(
        self,
        *,
        cookie_manager: Ticket12306CookieManager,
        max_concurrency: int = 8,
        request_timeout_seconds: float = 10.0,
        jitter_min_seconds: float = 0.05,
        jitter_max_seconds: float = 0.15,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._cookie_manager = cookie_manager
        self._semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self._request_timeout_seconds = request_timeout_seconds
        self._jitter_min_seconds = jitter_min_seconds
        self._jitter_max_seconds = jitter_max_seconds
        self._transport = transport

    async def fetch_leg(
        self,
        run_date: str,
        from_station: str,
        to_station: str,
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        async with self._semaphore:
            await self._jitter()
            try:
                return await self._do_fetch_leg(
                    run_date=run_date,
                    from_telecode=from_telecode,
                    to_telecode=to_telecode,
                    allow_retry=True,
                )
            except TicketHttpFailure:
                raise
            except Exception as exc:  # noqa: BLE001 - turn into TicketHttpFailure
                logger.warning(
                    "HTTP ticket fetch unexpected error %s→%s on %s: %s",
                    from_telecode,
                    to_telecode,
                    run_date,
                    exc,
                )
                raise TicketHttpFailure(str(exc)) from exc

    async def fetch_tickets(
        self,
        run_date: str,
        segments: set[SeatLookupKey],
        telecodes: dict[str, str],
        train_codes: dict[SeatLookupKey, str],
    ) -> dict[SeatLookupKey, TicketSegmentData]:
        leg_cache: dict[tuple[str, str], dict[str, Any]] = {}
        for _train_no, from_station, to_station in sorted(segments):
            leg = (from_station, to_station)
            if leg in leg_cache:
                continue
            from_code = telecodes.get(from_station)
            to_code = telecodes.get(to_station)
            if not from_code or not to_code:
                leg_cache[leg] = {}
                continue
            leg_cache[leg] = await self.fetch_leg(
                run_date,
                from_station,
                to_station,
                from_code,
                to_code,
            )

        result: dict[SeatLookupKey, TicketSegmentData] = {}
        for train_no, from_station, to_station in sorted(segments):
            leg = (from_station, to_station)
            rows = leg_cache.get(leg, {})
            if not rows:
                continue
            row = rows.get(train_no)
            matched_by = "train_no"
            if row is None:
                stc = train_codes.get((train_no, from_station, to_station), "")
                row = rows.get(stc)
                matched_by = "station_train_code"
            if row is None:
                continue
            seat_status, seat_prices = row
            seats = build_seat_infos(seat_status, seat_prices)
            result[(train_no, from_station, to_station)] = TicketSegmentData(
                seats=seats,
                min_price=segment_min_price(seats),
                matched_by=matched_by,
            )
        return result

    async def _do_fetch_leg(
        self,
        *,
        run_date: str,
        from_telecode: str,
        to_telecode: str,
        allow_retry: bool,
    ) -> dict[str, Any]:
        bundle = await self._cookie_manager.get()
        params = {
            "leftTicketDTO.train_date": run_date,
            "leftTicketDTO.from_station": from_telecode,
            "leftTicketDTO.to_station": to_telecode,
            "purpose_codes": "ADULT",
        }
        headers = dict(BASE_HEADERS)
        headers["User-Agent"] = bundle.user_agent

        client_kwargs: dict[str, Any] = {
            "timeout": self._request_timeout_seconds,
            "follow_redirects": False,
            "cookies": bundle.cookies,
            "headers": headers,
        }
        if self._transport is not None:
            client_kwargs["transport"] = self._transport

        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(LEFT_TICKET_QUERY_URL, params=params)
        except httpx.HTTPError as exc:
            if allow_retry:
                logger.info(
                    "HTTP ticket transient error %s→%s on %s: %s; retrying once",
                    from_telecode,
                    to_telecode,
                    run_date,
                    exc,
                )
                await asyncio.sleep(1.0)
                return await self._do_fetch_leg(
                    run_date=run_date,
                    from_telecode=from_telecode,
                    to_telecode=to_telecode,
                    allow_retry=False,
                )
            raise TicketHttpFailure(f"network error: {exc}") from exc

        # Redirects to login/init pages indicate cookie expiration / risk control.
        if 300 <= response.status_code < 400:
            return await self._handle_invalid_session(
                reason=f"redirect {response.status_code}",
                run_date=run_date,
                from_telecode=from_telecode,
                to_telecode=to_telecode,
                allow_retry=allow_retry,
            )

        if response.status_code >= 500:
            if allow_retry:
                logger.info(
                    "HTTP ticket %s→%s on %s returned %s; retrying once",
                    from_telecode,
                    to_telecode,
                    run_date,
                    response.status_code,
                )
                await asyncio.sleep(1.0)
                return await self._do_fetch_leg(
                    run_date=run_date,
                    from_telecode=from_telecode,
                    to_telecode=to_telecode,
                    allow_retry=False,
                )
            raise TicketHttpFailure(f"upstream {response.status_code}")

        if response.status_code != 200:
            raise TicketHttpFailure(f"unexpected status {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            return await self._handle_invalid_session(
                reason=f"non-json body: {exc}",
                run_date=run_date,
                from_telecode=from_telecode,
                to_telecode=to_telecode,
                allow_retry=allow_retry,
            )

        rows = parse_query_rows(payload)
        if rows:
            return rows

        # Empty result with status=true is normal for empty legs; only treat
        # explicit failure flags or empty-result-with-flag as risk control.
        if not isinstance(payload, dict) or not payload.get("status"):
            return await self._handle_invalid_session(
                reason="status=false",
                run_date=run_date,
                from_telecode=from_telecode,
                to_telecode=to_telecode,
                allow_retry=allow_retry,
            )
        return rows

    async def _handle_invalid_session(
        self,
        *,
        reason: str,
        run_date: str,
        from_telecode: str,
        to_telecode: str,
        allow_retry: bool,
    ) -> dict[str, Any]:
        await self._cookie_manager.mark_invalid()
        if allow_retry:
            logger.info(
                "HTTP ticket %s→%s on %s flagged (%s); refreshing cookies and retrying",
                from_telecode,
                to_telecode,
                run_date,
                reason,
            )
            await asyncio.sleep(0.5)
            return await self._do_fetch_leg(
                run_date=run_date,
                from_telecode=from_telecode,
                to_telecode=to_telecode,
                allow_retry=False,
            )
        raise TicketHttpFailure(f"session invalid: {reason}")

    async def _jitter(self) -> None:
        if self._jitter_max_seconds <= 0:
            return
        delay = random.uniform(self._jitter_min_seconds, self._jitter_max_seconds)
        if delay > 0:
            await asyncio.sleep(delay)


__all__ = ["HttpTicketClient", "TicketHttpFailure"]
