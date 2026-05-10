from __future__ import annotations

import asyncio
from typing import Any

from app.integrations.ticket_12306.client import (
    PlaywrightTicketClient,
    TicketClientConfig,
)
from app.integrations.ticket_12306.fallback_client import FallbackTicketClient
from app.integrations.ticket_12306.http_client import (
    HttpTicketClient,
    TicketHttpFailure,
)


class _StubHttpClient(HttpTicketClient):
    """Bypasses the real HTTP path; returns canned rows or raises on demand."""

    def __init__(self, *, rows: dict[str, Any] | None = None, exc: Exception | None = None) -> None:
        # Skip the parent constructor to avoid needing a cookie manager.
        self._rows = rows
        self._exc = exc
        self.calls = 0

    async def fetch_leg(  # type: ignore[override]
        self,
        run_date: str,
        from_station: str,
        to_station: str,
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        self.calls += 1
        if self._exc is not None:
            raise self._exc
        return self._rows or {}


class _StubPlaywrightClient(PlaywrightTicketClient):
    def __init__(self) -> None:
        # Sidestep the real ctor; we never need a browser.
        self.calls = 0
        self._config = TicketClientConfig()

    async def fetch_leg(  # type: ignore[override]
        self,
        run_date: str,
        from_station: str,
        to_station: str,
        from_telecode: str,
        to_telecode: str,
    ) -> dict[str, Any]:
        self.calls += 1
        return {"PLAYWRIGHT_TRAIN": ({"yz": "10"}, {"yz": 100.0})}


def _build_fallback(
    *,
    rows: dict[str, Any] | None = None,
    exc: Exception | None = None,
    failure_threshold: int = 3,
    open_seconds: float = 300.0,
) -> tuple[FallbackTicketClient, _StubHttpClient, _StubPlaywrightClient]:
    http = _StubHttpClient(rows=rows, exc=exc)
    playwright = _StubPlaywrightClient()
    fallback = FallbackTicketClient(
        http_client=http,
        playwright_client=playwright,
        failure_threshold=failure_threshold,
        open_seconds=open_seconds,
    )
    return fallback, http, playwright


def test_http_success_skips_playwright() -> None:
    fallback, http, playwright = _build_fallback(
        rows={"240000G1010A": ({"yz": "5"}, {"yz": 55.0})}
    )
    rows = asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    assert "240000G1010A" in rows
    assert http.calls == 1
    assert playwright.calls == 0


def test_http_failure_falls_back_to_playwright() -> None:
    fallback, http, playwright = _build_fallback(
        exc=TicketHttpFailure("session invalid")
    )
    rows = asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    assert "PLAYWRIGHT_TRAIN" in rows
    assert http.calls == 1
    assert playwright.calls == 1


def test_breaker_opens_after_threshold_consecutive_failures() -> None:
    fallback, http, playwright = _build_fallback(
        exc=TicketHttpFailure("session invalid"),
        failure_threshold=2,
        open_seconds=300.0,
    )

    asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    # After two failures the breaker should be open: HTTP is no longer tried.
    asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    assert http.calls == 2
    assert playwright.calls == 3


def test_breaker_resets_after_open_window_elapses() -> None:
    fallback, http, playwright = _build_fallback(
        exc=TicketHttpFailure("session invalid"),
        failure_threshold=1,
        open_seconds=0.0,  # immediately half-open on next call
    )

    asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    # Next call should retry HTTP because open_seconds=0 leaves the breaker
    # half-open immediately.
    asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    assert http.calls == 2
    assert playwright.calls == 2


def test_success_after_failure_resets_consecutive_counter() -> None:
    fallback, http, playwright = _build_fallback(
        exc=TicketHttpFailure("oops"), failure_threshold=2
    )

    # First call fails → falls back.
    asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    # Now flip the stub to succeed.
    http._exc = None
    http._rows = {"GOOD": ({"yz": "1"}, {"yz": 10.0})}

    rows = asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    assert "GOOD" in rows
    # Breaker should still be closed; one more failure should not yet open it.
    http._exc = TicketHttpFailure("oops")
    http._rows = None
    asyncio.run(
        fallback.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    assert http.calls == 3
    assert playwright.calls == 2  # not yet opened
