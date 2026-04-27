from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx

from app.integrations.ticket_12306.models import TicketSegmentData
from app.integrations.ticket_12306.parser import (
    BASE_HEADERS,
    LEFT_TICKET_QUERY_URL,
    build_seat_infos,
    parse_result_row,
    segment_min_price,
)
from app.models import SeatLookupKey
from app.system.settings_provider import SystemSettingsDataError, SystemSettingsProvider


@dataclass(frozen=True)
class TicketClientConfig:
    timeout_seconds: float = 20.0


class AbstractTicketClient(ABC):
    """票价查询客户端抽象基类。"""

    @abstractmethod
    async def fetch_tickets(
        self,
        run_date: str,
        segments: set[SeatLookupKey],
        telecodes: dict[str, str],
        train_codes: dict[SeatLookupKey, str],
    ) -> dict[SeatLookupKey, TicketSegmentData]:
        """查询指定区间的票价和余票信息。"""

    @abstractmethod
    async def fetch_leg(
        self,
        run_date: str,
        from_station: str,
        to_station: str,
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        """Query a single leg and return raw row data keyed by train_no and station_train_code."""


def _escape_station_name(name: str) -> str:
    escaped = []
    for ch in name.strip():
        codepoint = ord(ch)
        if codepoint > 0x7F:
            escaped.append(f"%u{codepoint:04X}")
        else:
            escaped.append(ch)
    return "".join(escaped)


def build_minimal_ticket_cookie(
    *,
    run_date: str,
    from_station: str,
    from_telecode: str,
    to_station: str,
    to_telecode: str,
) -> str:
    try:
        today = date.today().isoformat()
    except Exception:
        today = run_date

    cookie_items = [
        f"_jc_save_fromStation={_escape_station_name(from_station)}%2C{from_telecode}",
        f"_jc_save_toStation={_escape_station_name(to_station)}%2C{to_telecode}",
        "_jc_save_wfdc_flag=dc",
        f"_jc_save_fromDate={run_date}",
        f"_jc_save_toDate={today}",
        "guidesStatus=off",
        "highContrastMode=defaltMode",
        "cursorStatus=off",
    ]
    return "; ".join(cookie_items)


class Live12306TicketClient(AbstractTicketClient):
    """真实 12306 HTTP 客户端实现（异步）。"""

    def __init__(self, config: TicketClientConfig, http_client: httpx.AsyncClient) -> None:
        self._config = config
        self._http = http_client

    async def fetch_leg(
        self,
        run_date: str,
        from_station: str,
        to_station: str,
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        """Query a single leg and return raw row data keyed by train_no and station_train_code."""
        return await self._query_leg(
            run_date,
            from_station,
            to_station,
            from_telecode,
            to_telecode,
        )

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

    async def _query_leg(
        self,
        run_date: str,
        from_station: str,
        to_station: str,
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        params = {
            "leftTicketDTO.train_date": run_date,
            "leftTicketDTO.from_station": from_telecode,
            "leftTicketDTO.to_station": to_telecode,
            "purpose_codes": "ADULT",
        }
        headers = dict(BASE_HEADERS)
        headers["Cookie"] = build_minimal_ticket_cookie(
            run_date=run_date,
            from_station=from_station,
            from_telecode=from_telecode,
            to_station=to_station,
            to_telecode=to_telecode,
        )

        try:
            resp = await self._http.get(
                LEFT_TICKET_QUERY_URL,
                params=params,
                headers=headers,
                timeout=self._config.timeout_seconds,
                follow_redirects=False,
            )
            if resp.status_code == 302:
                return {}
            resp.raise_for_status()
            payload: dict[str, Any] = resp.json()
        except Exception:
            return {}

        if not payload.get("status"):
            return {}

        data = payload.get("data") or {}
        raw_results: list[str] = data.get("result") or []

        rows: dict[str, Any] = {}
        for raw in raw_results:
            if not isinstance(raw, str):
                continue
            train_no, stc, seat_status, seat_prices = parse_result_row(raw)
            entry = (seat_status, seat_prices)
            if train_no and train_no not in rows:
                rows[train_no] = entry
            if stc and stc not in rows:
                rows[stc] = entry
        return rows


async def build_ticket_client(
    settings_provider: SystemSettingsProvider,
    http_client: httpx.AsyncClient,
) -> AbstractTicketClient | None:
    try:
        enabled = await settings_provider.get_bool("ticket_12306_enabled")
    except SystemSettingsDataError:
        return None

    if not enabled:
        return None

    return Live12306TicketClient(
        config=TicketClientConfig(),
        http_client=http_client,
    )
