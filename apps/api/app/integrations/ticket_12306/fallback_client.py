from __future__ import annotations

import logging
from time import monotonic
from typing import Any

from app.integrations.ticket_12306.browser_manager import PlaywrightUnavailableError
from app.integrations.ticket_12306.client import (
    AbstractTicketClient,
    PlaywrightTicketClient,
)
from app.integrations.ticket_12306.http_client import HttpTicketClient, TicketHttpFailure
from app.integrations.ticket_12306.models import TicketSegmentData
from app.integrations.ticket_12306.parser import build_seat_infos, segment_min_price
from app.models import SeatLookupKey

logger = logging.getLogger(__name__)


class FallbackTicketClient(AbstractTicketClient):
    """Prefers HTTP, falls back to Playwright on failure with a simple breaker.

    After ``failure_threshold`` consecutive HTTP failures within a short
    window, the breaker opens and all traffic flows to Playwright for
    ``open_seconds`` before HTTP is probed again.
    """

    def __init__(
        self,
        *,
        http_client: HttpTicketClient,
        playwright_client: PlaywrightTicketClient,
        failure_threshold: int = 3,
        open_seconds: float = 300.0,
    ) -> None:
        self._http_client = http_client
        self._playwright_client = playwright_client
        self._failure_threshold = failure_threshold
        self._open_seconds = open_seconds
        self._consecutive_failures = 0
        self._open_until: float = 0.0

    async def fetch_leg(
        self,
        run_date: str,
        from_station: str,
        to_station: str,
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        if self._breaker_open():
            return await self._playwright_client.fetch_leg(
                run_date,
                from_station,
                to_station,
                from_telecode,
                to_telecode,
            )

        try:
            rows = await self._http_client.fetch_leg(
                run_date,
                from_station,
                to_station,
                from_telecode,
                to_telecode,
            )
        except TicketHttpFailure as exc:
            self._record_failure()
            logger.info(
                "HTTP ticket failed, falling back to Playwright (%s→%s on %s): %s",
                from_telecode,
                to_telecode,
                run_date,
                exc,
            )
            return await self._playwright_client.fetch_leg(
                run_date,
                from_station,
                to_station,
                from_telecode,
                to_telecode,
            )
        except PlaywrightUnavailableError:
            raise

        self._record_success()
        return rows

    async def fetch_tickets(
        self,
        run_date: str,
        segments: set[SeatLookupKey],
        telecodes: dict[str, str],
        train_codes: dict[SeatLookupKey, str],
    ) -> dict[SeatLookupKey, TicketSegmentData]:
        # Drive the leg cache through ``fetch_leg`` so the breaker / fallback
        # logic applies uniformly to every leg in the batch.
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

    def _breaker_open(self) -> bool:
        if self._open_until == 0.0:
            return False
        if monotonic() >= self._open_until:
            self._open_until = 0.0
            self._consecutive_failures = 0
            logger.info("HTTP ticket breaker half-open: probing HTTP path again")
            return False
        return True

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._failure_threshold:
            self._open_until = monotonic() + self._open_seconds
            logger.warning(
                "HTTP ticket breaker open for %.0fs after %d consecutive failures",
                self._open_seconds,
                self._consecutive_failures,
            )

    def _record_success(self) -> None:
        self._consecutive_failures = 0


__all__ = ["FallbackTicketClient"]
