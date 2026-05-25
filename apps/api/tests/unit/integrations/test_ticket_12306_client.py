from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from app.integrations.ticket_12306.client import (
    INIT_URL,
    ScraplingTicketClient,
    TicketLegRequest,
    build_ticket_client,
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


@dataclass
class FakePage:
    status: int
    payload: Any = None
    headers: dict[str, str] | None = None
    json_error: Exception | None = None

    def json(self) -> Any:
        if self.json_error is not None:
            raise self.json_error
        return self.payload


class FakeSession:
    def __init__(self, factory: FakeSessionFactory, session_id: int) -> None:
        self._factory = factory
        self.session_id = session_id
        self.init_calls = 0
        self.query_calls: list[dict[str, Any]] = []

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    async def get(self, url: str, **kwargs: Any) -> FakePage:
        await asyncio.sleep(0)
        if url == INIT_URL:
            self.init_calls += 1
            return FakePage(
                status=200,
                headers={"set-cookie": f"JSESSIONID=session-{self.session_id}"},
            )
        if url != LEFT_TICKET_QUERY_URL:
            raise AssertionError(f"unexpected url: {url}")

        self.query_calls.append(kwargs)
        params = kwargs["params"]
        key = (
            params["leftTicketDTO.train_date"],
            params["leftTicketDTO.from_station"],
            params["leftTicketDTO.to_station"],
        )
        response = self._factory.responses.get(key)
        if isinstance(response, Exception):
            raise response
        if response is not None:
            return response
        return FakePage(status=200, payload={"status": True, "data": {"result": [RAW_RESULT]}})


class FakeSessionFactory:
    def __init__(self) -> None:
        self.sessions: list[FakeSession] = []
        self.responses: dict[tuple[str, str, str], FakePage | Exception] = {}

    def __call__(self) -> FakeSession:
        session = FakeSession(self, len(self.sessions))
        self.sessions.append(session)
        return session


def _leg(index: int) -> TicketLegRequest:
    return TicketLegRequest(
        run_date="2026-04-28",
        from_station=f"from-{index}",
        to_station=f"to-{index}",
        from_telecode=f"F{index}",
        to_telecode=f"T{index}",
    )


def test_build_ticket_client_returns_none_when_setting_disabled() -> None:
    settings_provider = MagicMock()
    settings_provider.get_bool = AsyncMock(return_value=False)

    client = asyncio.run(build_ticket_client(settings_provider))

    assert client is None
    settings_provider.get_bool.assert_awaited_once_with("ticket_12306_enabled")


def test_build_ticket_client_returns_scrapling_client_when_setting_enabled() -> None:
    settings_provider = MagicMock()
    settings_provider.get_bool = AsyncMock(return_value=True)

    client = asyncio.run(build_ticket_client(settings_provider))

    assert isinstance(client, ScraplingTicketClient)
    settings_provider.get_bool.assert_awaited_once_with("ticket_12306_enabled")


def test_worker_count_boundaries() -> None:
    assert ScraplingTicketClient.calculate_worker_count(1) == 1
    assert ScraplingTicketClient.calculate_worker_count(100) == 1
    assert ScraplingTicketClient.calculate_worker_count(101) == 2
    assert ScraplingTicketClient.calculate_worker_count(1000) == 10
    assert ScraplingTicketClient.calculate_worker_count(1001) == 10


def test_fetch_legs_uses_worker_queue_and_reuses_worker_sessions() -> None:
    factory = FakeSessionFactory()
    client = ScraplingTicketClient(session_factory=factory, pause_seconds=0)
    legs = [_leg(i) for i in range(101)]

    results = asyncio.run(client.fetch_legs(legs))

    assert len(results) == 101
    assert len(factory.sessions) == 2
    assert all(session.init_calls == 1 for session in factory.sessions)
    assert sum(len(session.query_calls) for session in factory.sessions) == 101


def test_fetch_legs_parses_query_rows_and_passes_cookie_header() -> None:
    factory = FakeSessionFactory()
    client = ScraplingTicketClient(session_factory=factory, pause_seconds=0)
    leg = _leg(1)

    results = asyncio.run(client.fetch_legs([leg]))

    rows = results[leg.key]
    assert "240000G1010A" in rows
    assert "G1" in rows
    query = factory.sessions[0].query_calls[0]
    assert "JSESSIONID=session-0" in query["headers"]["Cookie"]


def test_fetch_legs_returns_empty_rows_for_failed_responses() -> None:
    factory = FakeSessionFactory()
    legs = [_leg(1), _leg(2), _leg(3)]
    factory.responses[(legs[0].run_date, legs[0].from_telecode, legs[0].to_telecode)] = (
        FakePage(status=302)
    )
    factory.responses[(legs[1].run_date, legs[1].from_telecode, legs[1].to_telecode)] = (
        FakePage(status=200, json_error=ValueError("bad json"))
    )
    factory.responses[(legs[2].run_date, legs[2].from_telecode, legs[2].to_telecode)] = (
        RuntimeError("network")
    )
    client = ScraplingTicketClient(session_factory=factory, pause_seconds=0)

    results = asyncio.run(client.fetch_legs(legs))

    assert results[legs[0].key] == {}
    assert results[legs[1].key] == {}
    assert results[legs[2].key] == {}


def test_fetch_legs_invokes_per_leg_callback() -> None:
    factory = FakeSessionFactory()
    client = ScraplingTicketClient(session_factory=factory, pause_seconds=0)
    legs = [_leg(1), _leg(2)]
    completed: list[tuple[str, str, str]] = []

    def on_leg_complete(leg: TicketLegRequest, rows: dict[str, Any]) -> None:
        assert rows
        completed.append(leg.key)

    asyncio.run(client.fetch_legs(legs, on_leg_complete=on_leg_complete))

    assert sorted(completed) == sorted(leg.key for leg in legs)
