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
    parse_query_rows,
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

            return parse_query_rows(payload)
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

async def build_ticket_client(
    settings_provider: SystemSettingsProvider,
    browser_manager: PlaywrightBrowserManager,
    *,
    redis_client: Any = None,
    cookie_pool: Any = None,
    proxy_pool: Any = None,
) -> AbstractTicketClient | None:
    """Build the production 12306 ticket client.

    Returns ``None`` when the feature flag is disabled or settings are
    unavailable.  When HTTP direct mode is enabled (``ticket_12306_http_enabled``)
    and a pre-created :class:`CookiePool` is provided, returns a
    :class:`FallbackTicketClient` that prefers HTTP and falls back to Playwright
    on failure.  Otherwise returns the legacy :class:`PlaywrightTicketClient`.

    An optional :class:`ProxyPool` can be supplied; when present, the HTTP
    client routes requests through rotating proxies to avoid IP rate-limiting.
    """
    try:
        enabled = await settings_provider.get_bool("ticket_12306_enabled")
    except SystemSettingsDataError:
        return None

    if not enabled:
        return None

    playwright_client = PlaywrightTicketClient(
        browser_manager=browser_manager,
        config=TicketClientConfig(),
    )

    if cookie_pool is None:
        return playwright_client

    try:
        http_enabled = await settings_provider.get_bool("ticket_12306_http_enabled")
    except SystemSettingsDataError:
        return playwright_client

    if not http_enabled:
        return playwright_client

    try:
        concurrency = await settings_provider.get_int("ticket_12306_http_concurrency")
    except SystemSettingsDataError:
        concurrency = 8

    # Lazy imports to avoid circular dependency: fallback_client imports this module.
    from app.integrations.ticket_12306.fallback_client import FallbackTicketClient
    from app.integrations.ticket_12306.http_client import HttpTicketClient

    http_client = HttpTicketClient(
        cookie_pool=cookie_pool,
        proxy_pool=proxy_pool,
        max_concurrency=max(1, concurrency),
    )
    return FallbackTicketClient(
        http_client=http_client,
        playwright_client=playwright_client,
    )


__all__ = [
    "AbstractTicketClient",
    "PlaywrightTicketClient",
    "PlaywrightUnavailableError",
    "TicketClientConfig",
    "build_ticket_client",
]
