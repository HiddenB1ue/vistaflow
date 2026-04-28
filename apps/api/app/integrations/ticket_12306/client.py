from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.integrations.ticket_12306.browser_manager import (
    PlaywrightBrowserManager,
    PlaywrightUnavailableError,
)
from app.integrations.ticket_12306.models import TicketSegmentData
from app.integrations.ticket_12306.parser import (
    LEFT_TICKET_QUERY_URL,
    build_seat_infos,
    parse_result_row,
    segment_min_price,
)
from app.models import SeatLookupKey
from app.system.settings_provider import SystemSettingsDataError, SystemSettingsProvider


@dataclass(frozen=True)
class TicketClientConfig:
    timeout_ms: int = 600_000


class AbstractTicketClient(ABC):
    """12306 票价查询客户端抽象基类。"""

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


class PlaywrightTicketClient(AbstractTicketClient):
    """12306 ticket client backed by a shared Playwright Chromium browser."""

    def __init__(
        self,
        *,
        browser_manager: PlaywrightBrowserManager,
        config: TicketClientConfig,
    ) -> None:
        self._browser_manager = browser_manager
        self._config = config

    async def fetch_leg(
        self,
        run_date: str,
        from_station: str,
        to_station: str,
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        return await self._browser_manager.run_with_browser(
            lambda browser: self._fetch_leg_with_browser(
                browser=browser,
                run_date=run_date,
                from_station=from_station,
                to_station=to_station,
                from_telecode=from_telecode,
                to_telecode=to_telecode,
            )
        )

    async def _fetch_leg_with_browser(
        self,
        *,
        browser: Any,
        run_date: str,
        from_station: str,
        to_station: str,
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        context = await browser.new_context(
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        try:
            page = await context.new_page()
            page.set_default_timeout(self._config.timeout_ms)
            page.set_default_navigation_timeout(self._config.timeout_ms)

            await page.goto(
                "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc",
                wait_until="domcontentloaded",
                timeout=self._config.timeout_ms,
            )
            await page.wait_for_load_state("networkidle", timeout=self._config.timeout_ms)

            await page.locator("input#fromStationText").fill(from_station)
            await page.locator("input#toStationText").fill(to_station)
            await page.locator("input#train_date").fill(run_date)
            await page.evaluate(
                """({fromName, fromCode, toName, toCode, runDate}) => {
                    const setValue = (id, value) => {
                        const el = document.getElementById(id);
                        if (!el) return;
                        el.value = value;
                        el.dispatchEvent(new Event("input", { bubbles: true }));
                        el.dispatchEvent(new Event("change", { bubbles: true }));
                    };
                    setValue("fromStationText", fromName);
                    setValue("fromStation", fromCode);
                    setValue("toStationText", toName);
                    setValue("toStation", toCode);
                    setValue("train_date", runDate);
                    setValue("back_train_date", runDate);
                }""",
                {
                    "fromName": from_station,
                    "fromCode": from_telecode,
                    "toName": to_station,
                    "toCode": to_telecode,
                    "runDate": run_date,
                },
            )

            try:
                async with page.expect_response(
                    lambda response: (
                        response.request.method == "GET"
                        and response.url.startswith(LEFT_TICKET_QUERY_URL)
                    ),
                    timeout=self._config.timeout_ms,
                ) as response_info:
                    await page.locator("#query_ticket").click()
                response = await response_info.value
                payload = await response.json()
            except Exception:
                return {}

            return self._parse_query_rows(payload)
        finally:
            await context.close()

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

    def _parse_query_rows(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict) or not payload.get("status"):
            return {}

        data = payload.get("data")
        if not isinstance(data, dict):
            return {}

        raw_results = data.get("result")
        if not isinstance(raw_results, list):
            return {}

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
    browser_manager: PlaywrightBrowserManager,
) -> AbstractTicketClient | None:
    try:
        enabled = await settings_provider.get_bool("ticket_12306_enabled")
    except SystemSettingsDataError:
        return None

    if not enabled:
        return None

    return PlaywrightTicketClient(
        browser_manager=browser_manager,
        config=TicketClientConfig(),
    )


__all__ = [
    "AbstractTicketClient",
    "PlaywrightTicketClient",
    "PlaywrightUnavailableError",
    "TicketClientConfig",
    "build_ticket_client",
]
