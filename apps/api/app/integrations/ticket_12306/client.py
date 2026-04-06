from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from app.integrations.ticket_12306.models import TicketSegmentData
from app.integrations.ticket_12306.parser import (
    BASE_HEADERS,
    LEFT_TICKET_BASE,
    build_seat_infos,
    parse_result_row,
    segment_min_price,
)
from app.models import SeatLookupKey


@dataclass(frozen=True)
class TicketClientConfig:
    endpoint: str = "queryG"
    cookie: str = ""
    timeout_seconds: float = 20.0


class AbstractTicketClient(ABC):
    """票价查询客户端抽象基类。Service 层只依赖此接口。"""

    @abstractmethod
    async def fetch_tickets(
        self,
        run_date: str,
        segments: set[SeatLookupKey],
        telecodes: dict[str, str],
        train_codes: dict[SeatLookupKey, str],
    ) -> dict[SeatLookupKey, TicketSegmentData]:
        """查询指定区间的票价和余票信息。

        Args:
            run_date: 出行日期，格式 YYYY-MM-DD。
            segments: 需要查询的区间集合 (train_no, from_station, to_station)。
            telecodes: 站名 → 电报码映射。
            train_codes: 区间 → station_train_code 映射（用于兜底匹配）。

        Returns:
            已成功查询到数据的区间 → TicketSegmentData。
        """


class NullTicketClient(AbstractTicketClient):
    """空实现：enable_ticket_enrich=False 时使用，直接返回空结果。"""

    async def fetch_tickets(
        self,
        run_date: str,
        segments: set[SeatLookupKey],
        telecodes: dict[str, str],
        train_codes: dict[SeatLookupKey, str],
    ) -> dict[SeatLookupKey, TicketSegmentData]:
        return {}


class Live12306TicketClient(AbstractTicketClient):
    """真实 12306 HTTP 客户端实现（异步）。"""

    def __init__(self, config: TicketClientConfig, http_client: httpx.AsyncClient) -> None:
        self._config = config
        self._http = http_client

    async def fetch_tickets(
        self,
        run_date: str,
        segments: set[SeatLookupKey],
        telecodes: dict[str, str],
        train_codes: dict[SeatLookupKey, str],
    ) -> dict[SeatLookupKey, TicketSegmentData]:
        # 按区间分组，每个唯一 (from, to) 只查一次 12306
        leg_cache: dict[tuple[str, str], dict[str, Any]] = {}
        for _train_no, from_station, to_station in sorted(segments):
            leg = (from_station, to_station)
            if leg in leg_cache:
                continue
            from_code = telecodes.get(from_station)
            to_code = telecodes.get(to_station)
            if not from_code or not to_code:
                leg_cache[leg] = {}  # 无电报码，跳过
                continue
            leg_cache[leg] = await self._query_leg(run_date, from_code, to_code)

        result: dict[SeatLookupKey, TicketSegmentData] = {}
        for train_no, from_station, to_station in sorted(segments):
            leg = (from_station, to_station)
            rows = leg_cache.get(leg, {})
            if not rows:
                continue

            # 优先按 train_no 匹配，其次按 station_train_code
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
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        """查询单条区间，返回 {train_no_or_code: (seat_status, seat_prices)}。"""
        url = f"{LEFT_TICKET_BASE}/{self._config.endpoint}"
        params = {
            "leftTicketDTO.train_date": run_date,
            "leftTicketDTO.from_station": from_telecode,
            "leftTicketDTO.to_station": to_telecode,
            "purpose_codes": "ADULT",
        }
        headers = dict(BASE_HEADERS)
        if self._config.cookie.strip():
            headers["Cookie"] = self._config.cookie.strip()

        try:
            resp = await self._http.get(
                url,
                params=params,
                headers=headers,
                timeout=self._config.timeout_seconds,
                follow_redirects=False,
            )
            if resp.status_code == 302:
                return {}  # Cookie 过期，静默跳过
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
