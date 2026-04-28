from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from app.integrations.ticket_12306.client import (
    PlaywrightTicketClient,
    TicketClientConfig,
    build_ticket_client,
)

RAW_RESULT = "|".join(
    [
        "",
        "",
        "240000G1010A",
        "G1",
        "",
        "",
        "BJP",
        "SHH",
        "07:00",
        "12:30",
        "05:30",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "--",
        "",
        "",
        "",
        "",
        "--",
        "5",
        "",
        "",
        "",
        "5",
        "2",
        "1",
        "",
        "",
        "",
        "",
        "",
        "",
        "M009900000O005530000W005530000",
    ]
)


@dataclass
class FakeResponse:
    payload: dict[str, Any]

    async def json(self) -> dict[str, Any]:
        return self.payload


class FakeResponseInfo:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.value: asyncio.Future[FakeResponse] = asyncio.Future()
        self.value.set_result(FakeResponse(payload))


class FakeExpectResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    async def __aenter__(self) -> FakeResponseInfo:
        return FakeResponseInfo(self._payload)

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakeLocator:
    def __init__(self) -> None:
        self.filled_values: list[str] = []
        self.click_count = 0

    async def fill(self, value: str) -> None:
        self.filled_values.append(value)

    async def click(self) -> None:
        self.click_count += 1


class FakePage:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.locators: dict[str, FakeLocator] = {}
        self.goto_calls: list[tuple[str, str, int]] = []
        self.wait_for_load_state_calls: list[tuple[str, int]] = []
        self.evaluate_calls: list[dict[str, Any]] = []
        self.timeout_ms: int | None = None
        self.navigation_timeout_ms: int | None = None

    def set_default_timeout(self, timeout_ms: int) -> None:
        self.timeout_ms = timeout_ms

    def set_default_navigation_timeout(self, timeout_ms: int) -> None:
        self.navigation_timeout_ms = timeout_ms

    async def goto(self, url: str, *, wait_until: str, timeout: int) -> None:
        self.goto_calls.append((url, wait_until, timeout))

    async def wait_for_load_state(self, state: str, *, timeout: int) -> None:
        self.wait_for_load_state_calls.append((state, timeout))

    def locator(self, selector: str) -> FakeLocator:
        locator = self.locators.get(selector)
        if locator is None:
            locator = FakeLocator()
            self.locators[selector] = locator
        return locator

    async def evaluate(self, expression: str, arg: dict[str, Any]) -> None:
        self.evaluate_calls.append({"expression": expression, "arg": arg})

    def expect_response(self, predicate, *, timeout: int) -> FakeExpectResponse:
        return FakeExpectResponse(self._payload)


class FakeContext:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.page = FakePage(payload)
        self.closed = False

    async def new_page(self) -> FakePage:
        return self.page

    async def close(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.contexts: list[FakeContext] = []

    async def new_context(self, **kwargs: Any) -> FakeContext:
        context = FakeContext(self.payload)
        self.contexts.append(context)
        return context


class FakeBrowserManager:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.browser = FakeBrowser(payload)
        self.calls = 0

    async def get_browser(self) -> FakeBrowser:
        self.calls += 1
        return self.browser

    async def run_with_browser(self, callback):
        self.calls += 1
        return await callback(self.browser)


def _make_payload(result: list[Any]) -> dict[str, Any]:
    return {"status": True, "data": {"result": result}}


def test_build_ticket_client_returns_none_when_setting_disabled() -> None:
    settings_provider = MagicMock()
    settings_provider.get_bool = AsyncMock(return_value=False)
    browser_manager = MagicMock()

    client = asyncio.run(build_ticket_client(settings_provider, browser_manager))

    assert client is None
    settings_provider.get_bool.assert_awaited_once_with("ticket_12306_enabled")


def test_build_ticket_client_returns_playwright_client_when_setting_enabled() -> None:
    settings_provider = MagicMock()
    settings_provider.get_bool = AsyncMock(return_value=True)
    browser_manager = MagicMock()

    client = asyncio.run(build_ticket_client(settings_provider, browser_manager))

    assert isinstance(client, PlaywrightTicketClient)
    settings_provider.get_bool.assert_awaited_once_with("ticket_12306_enabled")


def test_fetch_leg_builds_rows_from_queryg_payload() -> None:
    payload = _make_payload([RAW_RESULT])
    browser_manager = FakeBrowserManager(payload)
    client = PlaywrightTicketClient(
        browser_manager=browser_manager,
        config=TicketClientConfig(timeout_ms=15_000),
    )

    rows = asyncio.run(
        client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )

    assert "240000G1010A" in rows
    assert "G1" in rows
    seat_status, seat_prices = rows["240000G1010A"]
    assert seat_status["wz"] == "5"
    assert seat_prices["zy"] == 99.0
    assert seat_prices["ze"] == 55.3

    page = browser_manager.browser.contexts[0].page
    assert page.locators["input#fromStationText"].filled_values == ["Beijing"]
    assert page.locators["input#toStationText"].filled_values == ["Shanghai"]
    assert page.locators["input#train_date"].filled_values == ["2026-04-28"]
    assert page.locators["#query_ticket"].click_count == 1
    assert browser_manager.browser.contexts[0].closed is True


def test_fetch_leg_returns_empty_on_invalid_payload() -> None:
    browser_manager = FakeBrowserManager({"status": False, "data": {"result": [RAW_RESULT]}})
    client = PlaywrightTicketClient(
        browser_manager=browser_manager,
        config=TicketClientConfig(),
    )

    rows = asyncio.run(
        client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )

    assert rows == {}


def test_fetch_leg_returns_empty_when_results_structure_is_invalid() -> None:
    browser_manager = FakeBrowserManager({"status": True, "data": {"result": "bad"}})
    client = PlaywrightTicketClient(
        browser_manager=browser_manager,
        config=TicketClientConfig(),
    )

    rows = asyncio.run(
        client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )

    assert rows == {}
