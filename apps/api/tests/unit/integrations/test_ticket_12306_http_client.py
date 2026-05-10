from __future__ import annotations

import asyncio

import httpx
import pytest

from app.integrations.ticket_12306.cookie_manager import CookieBundle
from app.integrations.ticket_12306.http_client import (
    HttpTicketClient,
    TicketHttpFailure,
)
from app.integrations.ticket_12306.parser import LEFT_TICKET_QUERY_URL

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


class StubCookieManager:
    def __init__(self) -> None:
        self.bundle = CookieBundle(
            cookies={"JSESSIONID": "abc", "BIGipServerotn": "xyz"},
            user_agent="ua",
            refreshed_at=1.0,
        )
        self.invalidated = 0

    async def get(self) -> CookieBundle:
        return self.bundle

    async def mark_invalid(self) -> None:
        self.invalidated += 1


def _build_client(
    transport: httpx.MockTransport,
    *,
    cookie_manager: StubCookieManager | None = None,
) -> tuple[HttpTicketClient, StubCookieManager]:
    cm = cookie_manager or StubCookieManager()
    client = HttpTicketClient(
        cookie_manager=cm,  # type: ignore[arg-type]
        max_concurrency=2,
        jitter_min_seconds=0.0,
        jitter_max_seconds=0.0,
        transport=transport,
    )
    return client, cm


def test_fetch_leg_returns_rows_on_success() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={"status": True, "data": {"result": [RAW_RESULT]}},
        )

    client, cm = _build_client(httpx.MockTransport(handler))
    rows = asyncio.run(
        client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )

    assert "240000G1010A" in rows
    assert seen
    request = seen[0]
    assert str(request.url).startswith(LEFT_TICKET_QUERY_URL)
    assert request.url.params["leftTicketDTO.train_date"] == "2026-04-28"
    assert request.url.params["leftTicketDTO.from_station"] == "BJP"
    assert request.url.params["leftTicketDTO.to_station"] == "SHH"
    assert request.url.params["purpose_codes"] == "ADULT"
    cookie_header = request.headers.get("cookie", "")
    assert "JSESSIONID=abc" in cookie_header
    assert cm.invalidated == 0


def test_fetch_leg_invalidates_cookies_and_retries_on_status_false() -> None:
    calls = {"count": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(200, json={"status": False, "messages": ["oops"]})
        return httpx.Response(
            200,
            json={"status": True, "data": {"result": [RAW_RESULT]}},
        )

    client, cm = _build_client(httpx.MockTransport(handler))
    rows = asyncio.run(
        client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )

    assert "240000G1010A" in rows
    assert calls["count"] == 2
    assert cm.invalidated == 1


def test_fetch_leg_raises_after_second_failure() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": False})

    client, cm = _build_client(httpx.MockTransport(handler))
    with pytest.raises(TicketHttpFailure):
        asyncio.run(
            client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
        )
    assert cm.invalidated == 2


def test_fetch_leg_retries_on_5xx_then_succeeds() -> None:
    calls = {"count": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={"status": True, "data": {"result": [RAW_RESULT]}},
        )

    client, cm = _build_client(httpx.MockTransport(handler))
    rows = asyncio.run(
        client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )

    assert "240000G1010A" in rows
    assert calls["count"] == 2
    assert cm.invalidated == 0


def test_fetch_leg_treats_redirect_as_session_invalid() -> None:
    calls = {"count": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(302, headers={"Location": "/otn/login/init"})

    client, cm = _build_client(httpx.MockTransport(handler))
    with pytest.raises(TicketHttpFailure, match="session invalid"):
        asyncio.run(
            client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
        )
    assert calls["count"] == 2
    assert cm.invalidated == 2


def test_fetch_leg_wraps_network_error_as_http_failure() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    client, _ = _build_client(httpx.MockTransport(handler))
    with pytest.raises(TicketHttpFailure, match="network error"):
        asyncio.run(
            client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
        )


def test_fetch_leg_returns_empty_when_status_true_but_result_empty() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": True, "data": {"result": []}})

    client, cm = _build_client(httpx.MockTransport(handler))
    rows = asyncio.run(
        client.fetch_leg("2026-04-28", "Beijing", "Shanghai", "BJP", "SHH")
    )
    assert rows == {}
    # status=true with empty result is a normal "no trains" leg, not risk control.
    assert cm.invalidated == 0


def test_fetch_tickets_groups_by_leg_and_dedupes_calls() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={"status": True, "data": {"result": [RAW_RESULT]}},
        )

    client, _ = _build_client(httpx.MockTransport(handler))
    segments = {
        ("240000G1010A", "Beijing", "Shanghai"),
        ("240000G3010A", "Beijing", "Shanghai"),  # same leg, different train
    }
    telecodes = {"Beijing": "BJP", "Shanghai": "SHH"}
    train_codes = {
        ("240000G1010A", "Beijing", "Shanghai"): "G1",
        ("240000G3010A", "Beijing", "Shanghai"): "G3",
    }

    result = asyncio.run(
        client.fetch_tickets(
            run_date="2026-04-28",
            segments=segments,
            telecodes=telecodes,
            train_codes=train_codes,
        )
    )

    # One physical leg call regardless of how many trains share the leg.
    assert len(calls) == 1
    # Only the train_no actually present in the parsed payload is matched.
    assert ("240000G1010A", "Beijing", "Shanghai") in result
