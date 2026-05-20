from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

import httpx

from app.integrations.ticket_12306.client import AbstractTicketClient
from app.integrations.ticket_12306.cookie_manager import CookieBundle
from app.integrations.ticket_12306.cookie_pool import CookiePool
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

# Backoff seconds for consecutive redirect retries (index 0 = first retry).
_REDIRECT_BACKOFF_SECONDS = (2.0, 5.0, 10.0)
_MAX_REDIRECT_RETRIES = len(_REDIRECT_BACKOFF_SECONDS)

# After seeing a redirect, all requests pause for this duration before hitting
# the 12306 endpoint again.  This prevents other concurrent requests from also
# burning through the rate-limit window.
_IP_COOLDOWN_SECONDS = 3.0


class TicketHttpFailure(Exception):
    """HTTP path failed in a way that should trigger Playwright fallback."""


class HttpTicketClient(AbstractTicketClient):
    """12306 ticket client that talks to ``leftTicket/queryG`` over HTTP.

    Uses cookies from a :class:`CookiePool`. On failure signals
    such as ``status=false``, redirects, or 5xx responses, performs a single
    in-place retry after refreshing cookies. If retry still fails, raises
    :class:`TicketHttpFailure` so the fallback layer can switch to Playwright.
    """

    def __init__(
        self,
        *,
        cookie_pool: CookiePool,
        max_concurrency: int = 8,
        request_timeout_seconds: float = 10.0,
        jitter_min_seconds: float = 0.05,
        jitter_max_seconds: float = 0.15,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._cookie_pool = cookie_pool
        self._semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self._request_timeout_seconds = request_timeout_seconds
        self._jitter_min_seconds = jitter_min_seconds
        self._jitter_max_seconds = jitter_max_seconds
        self._transport = transport
        # Shared IP-level cooldown: monotonic timestamp of last redirect.
        self._last_redirect_ts: float = 0.0

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

    async def _respect_ip_cooldown(self) -> None:
        """Wait if a recent redirect suggests the IP is rate-limited."""
        elapsed = time.monotonic() - self._last_redirect_ts
        if elapsed < _IP_COOLDOWN_SECONDS:
            await asyncio.sleep(_IP_COOLDOWN_SECONDS - elapsed)

    async def _do_fetch_leg(
        self,
        *,
        run_date: str,
        from_telecode: str,
        to_telecode: str,
        allow_retry: bool,
        bundle: CookieBundle | None = None,
        redirect_attempt: int = 0,
    ) -> dict[str, Any]:
        if bundle is None:
            bundle = await self._cookie_pool.get()

        await self._respect_ip_cooldown()

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
                    bundle=bundle,
                )
            raise TicketHttpFailure(f"network error: {exc}") from exc

        # ---- Redirect: likely IP-level rate limiting, NOT cookie death ----
        if 300 <= response.status_code < 400:
            self._last_redirect_ts = time.monotonic()
            return await self._handle_redirect(
                bundle=bundle,
                status_code=response.status_code,
                run_date=run_date,
                from_telecode=from_telecode,
                to_telecode=to_telecode,
                redirect_attempt=redirect_attempt,
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
                    bundle=bundle,
                )
            raise TicketHttpFailure(f"upstream {response.status_code}")

        if response.status_code != 200:
            raise TicketHttpFailure(f"unexpected status {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            return await self._handle_cookie_invalid(
                bundle=bundle,
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
            return await self._handle_cookie_invalid(
                bundle=bundle,
                reason="status=false",
                run_date=run_date,
                from_telecode=from_telecode,
                to_telecode=to_telecode,
                allow_retry=allow_retry,
            )
        return rows

    # ---- Redirect handling: IP rate-limit, keep cookie, backoff ----

    async def _handle_redirect(
        self,
        *,
        bundle: CookieBundle,
        status_code: int,
        run_date: str,
        from_telecode: str,
        to_telecode: str,
        redirect_attempt: int,
    ) -> dict[str, Any]:
        """Handle 3xx redirect with backoff.  Does NOT invalidate cookies."""
        if redirect_attempt < _MAX_REDIRECT_RETRIES:
            delay = _REDIRECT_BACKOFF_SECONDS[redirect_attempt]
            logger.info(
                "HTTP ticket %s→%s on %s got %s (IP rate limit); "
                "backoff %.0fs then retry (#%d/%d)",
                from_telecode,
                to_telecode,
                run_date,
                status_code,
                delay,
                redirect_attempt + 1,
                _MAX_REDIRECT_RETRIES,
            )
            await asyncio.sleep(delay)
            return await self._do_fetch_leg(
                run_date=run_date,
                from_telecode=from_telecode,
                to_telecode=to_telecode,
                allow_retry=False,
                bundle=bundle,
                redirect_attempt=redirect_attempt + 1,
            )
        # Exhausted redirect retries – invalidate cookie as last resort.
        await self._cookie_pool.mark_invalid(bundle)
        raise TicketHttpFailure(
            f"redirect {status_code} persisted after {_MAX_REDIRECT_RETRIES} retries"
        )

    # ---- Cookie-invalid handling: status=false / non-JSON ----

    async def _handle_cookie_invalid(
        self,
        *,
        bundle: CookieBundle,
        reason: str,
        run_date: str,
        from_telecode: str,
        to_telecode: str,
        allow_retry: bool,
    ) -> dict[str, Any]:
        """Handle genuine cookie/session invalidation."""
        await self._cookie_pool.mark_invalid(bundle)
        if allow_retry:
            logger.info(
                "HTTP ticket %s→%s on %s flagged (%s); "
                "switching cookie slot and retrying",
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
                bundle=None,
            )
        raise TicketHttpFailure(f"session invalid: {reason}")

    async def _jitter(self) -> None:
        if self._jitter_max_seconds <= 0:
            return
        delay = random.uniform(self._jitter_min_seconds, self._jitter_max_seconds)
        if delay > 0:
            await asyncio.sleep(delay)


__all__ = ["HttpTicketClient", "TicketHttpFailure"]
