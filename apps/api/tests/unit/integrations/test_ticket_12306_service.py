from __future__ import annotations

import json
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

from app.integrations.ticket_12306.client import TicketLegRequest
from app.integrations.ticket_12306.service import Ticket12306Service
from app.journey_search_sessions.schemas import (
    CachedRouteCandidate,
    CachedTrainSegment,
    PriceCacheEntry,
    RouteStationResponse,
    RouteTransferSegmentResponse,
    price_map_key,
)


def _station(name: str) -> RouteStationResponse:
    return RouteStationResponse(name=name, code="", city="", lng=0.0, lat=0.0)


def _train_seg(
    train_no: str,
    no: str,
    origin_name: str,
    dest_name: str,
    departure_date: str = "2025-01-01",
) -> CachedTrainSegment:
    return CachedTrainSegment(
        trainNo=train_no,
        no=no,
        origin=_station(origin_name),
        destination=_station(dest_name),
        departureDate=departure_date,
        departureTime="08:00",
        arrivalDate=departure_date,
        arrivalTime="10:00",
    )


def _candidate(
    segs: list[CachedTrainSegment | RouteTransferSegmentResponse],
    candidate_id: str = "c1",
) -> CachedRouteCandidate:
    first_train = next((s for s in segs if isinstance(s, CachedTrainSegment)), None)
    origin = first_train.origin if first_train else _station("A")
    dest = first_train.destination if first_train else _station("B")
    return CachedRouteCandidate(
        id=candidate_id,
        trainNo=first_train.trainNo if first_train else "",
        type="direct",
        origin=origin,
        destination=dest,
        departureDate=first_train.departureDate if first_train else "2025-01-01",
        departureTime="08:00",
        arrivalDate=first_train.arrivalDate if first_train else "2025-01-01",
        arrivalTime="10:00",
        durationMinutes=120,
        segs=segs,
        pathPoints=[],
        isDirect=True,
        transferCount=0,
    )


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def mget(self, keys: list[str]) -> list[str | None]:
        return [self.store.get(k) for k in keys]

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        self.store[key] = value
        self.ttls[key] = ttl
        return True


class FakeStationRepo:
    def __init__(self, telecodes: dict[str, str]) -> None:
        self._telecodes = telecodes

    async def get_telecodes_by_names(self, names: set[str]) -> dict[str, str]:
        return {name: self._telecodes[name] for name in names if name in self._telecodes}


class FakeBatchTicketClient:
    def __init__(
        self,
        *,
        default_rows: dict[str, Any] | None = None,
        rows_by_leg: dict[tuple[str, str, str], dict[str, Any]] | None = None,
    ) -> None:
        self.default_rows = default_rows or {}
        self.rows_by_leg = rows_by_leg or {}
        self.calls: list[list[TicketLegRequest]] = []

    async def fetch_legs(
        self,
        legs: list[TicketLegRequest],
        *,
        on_leg_complete: Any = None,
    ) -> dict[tuple[str, str, str], dict[str, Any]]:
        self.calls.append(list(legs))
        result: dict[tuple[str, str, str], dict[str, Any]] = {}
        for leg in legs:
            rows = self.rows_by_leg.get(leg.key, self.default_rows)
            result[leg.key] = rows
            if on_leg_complete is not None:
                maybe = on_leg_complete(leg, rows)
                if maybe is not None:
                    await maybe
        return result


def _make_rows(
    train_no: str,
    stc: str,
    seat_status: dict[str, str] | None = None,
    seat_prices: dict[str, float] | None = None,
) -> dict[str, Any]:
    entry = (seat_status or {"ze": "5", "zy": "2"}, seat_prices or {"ze": 55.5, "zy": 99.0})
    rows: dict[str, Any] = {}
    if train_no:
        rows[train_no] = entry
    if stc:
        rows[stc] = entry
    return rows


@pytest.fixture
def redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def station_repo() -> FakeStationRepo:
    return FakeStationRepo({
        "A": "AAA",
        "B": "BBB",
        "C": "CCC",
    })


def _build_service(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
    ticket_client: Any = None,
) -> Ticket12306Service:
    return Ticket12306Service(
        redis_client=cast(Any, redis),
        station_repo=cast(Any, station_repo),
        ticket_client=ticket_client,
        cache_ttl_seconds=60,
        failure_ttl_seconds=10,
    )


async def test_returns_empty_when_no_ticket_client(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
) -> None:
    service = _build_service(redis, station_repo, ticket_client=None)
    candidates = [_candidate([_train_seg("T1", "G1", "A", "B")])]

    result = await service.prefetch_all_prices(run_date="2025-01-01", candidates=candidates)

    assert result == {}


async def test_basic_prefetch_returns_price_map_and_uses_segment_departure_date(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
) -> None:
    client = FakeBatchTicketClient(default_rows=_make_rows("T1", "G1"))
    service = _build_service(redis, station_repo, ticket_client=client)
    candidates = [_candidate([_train_seg("T1", "G1", "A", "B", "2025-01-02")])]

    result = await service.prefetch_all_prices(run_date="2025-01-01", candidates=candidates)

    key = price_map_key("T1", "A", "B")
    assert result[key].failed is False
    assert result[key].min_price == 55.5
    assert client.calls[0][0].run_date == "2025-01-02"
    assert client.calls[0][0].from_telecode == "AAA"
    assert "journey_search:ticket_segment:v3:2025-01-02:A:B" in redis.store


async def test_deduplicates_unique_leg_date_keys(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
) -> None:
    rows = _make_rows("T1", "G1")
    rows["T2"] = rows["T1"]
    rows["G2"] = rows["T1"]
    client = FakeBatchTicketClient(default_rows=rows)
    service = _build_service(redis, station_repo, ticket_client=client)
    candidates = [
        _candidate([_train_seg("T1", "G1", "A", "B")], "c1"),
        _candidate([_train_seg("T2", "G2", "A", "B")], "c2"),
    ]

    await service.prefetch_all_prices(run_date="2025-01-01", candidates=candidates)

    assert len(client.calls) == 1
    assert len(client.calls[0]) == 1


async def test_cache_hit_skips_fetch(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
) -> None:
    client = FakeBatchTicketClient(default_rows=_make_rows("T1", "G1"))
    service = _build_service(redis, station_repo, ticket_client=client)
    redis.store["journey_search:ticket_segment:v3:2025-01-01:A:B"] = json.dumps({
        "T1": {"seats": [["ze", "5", 55.5, 1]], "min_price": 55.5},
    })
    candidates = [_candidate([_train_seg("T1", "G1", "A", "B")])]

    result = await service.prefetch_all_prices(run_date="2025-01-01", candidates=candidates)

    assert client.calls == []
    assert result[price_map_key("T1", "A", "B")].failed is False


async def test_cache_miss_stores_all_trains_from_leg_response(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
) -> None:
    rows = _make_rows("T1", "G1")
    rows["T2_LONGFORM"] = ({"ze": "8"}, {"ze": 70.0})
    rows["G2"] = rows["T2_LONGFORM"]
    client = FakeBatchTicketClient(default_rows=rows)
    service = _build_service(redis, station_repo, ticket_client=client)
    candidates = [_candidate([_train_seg("T1", "G1", "A", "B")])]

    await service.prefetch_all_prices(run_date="2025-01-01", candidates=candidates)

    raw = redis.store["journey_search:ticket_segment:v3:2025-01-01:A:B"]
    payload = json.loads(raw)
    assert "T1" in payload
    assert "T2_LONGFORM" in payload


async def test_empty_rows_write_failure_cache_and_return_failed_price(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
) -> None:
    client = FakeBatchTicketClient(default_rows={})
    service = _build_service(redis, station_repo, ticket_client=client)
    candidates = [_candidate([_train_seg("T1", "G1", "A", "B")])]

    result = await service.prefetch_all_prices(run_date="2025-01-01", candidates=candidates)

    cache_key = "journey_search:ticket_segment:v3:2025-01-01:A:B"
    assert redis.store[cache_key] == ""
    assert redis.ttls[cache_key] == 10
    assert result[price_map_key("T1", "A", "B")].failed is True


async def test_transfer_segments_are_skipped(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
) -> None:
    rows_by_leg = {
        ("2025-01-01", "A", "C"): _make_rows("T1", "G1"),
        ("2025-01-01", "C", "B"): _make_rows("T2", "G2"),
    }
    client = FakeBatchTicketClient(rows_by_leg=rows_by_leg)
    service = _build_service(redis, station_repo, ticket_client=client)
    candidates = [
        _candidate([
            _train_seg("T1", "G1", "A", "C"),
            RouteTransferSegmentResponse(transfer="C"),
            _train_seg("T2", "G2", "C", "B"),
        ])
    ]

    result = await service.prefetch_all_prices(run_date="2025-01-01", candidates=candidates)

    assert len(client.calls[0]) == 2
    assert price_map_key("T1", "A", "C") in result
    assert price_map_key("T2", "C", "B") in result
    assert len(result) == 2


async def test_matches_by_station_train_code_fallback(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
) -> None:
    client = FakeBatchTicketClient(default_rows={"G1": ({"ze": "5"}, {"ze": 55.5})})
    service = _build_service(redis, station_repo, ticket_client=client)
    candidates = [_candidate([_train_seg("T1", "G1", "A", "B")])]

    result = await service.prefetch_all_prices(run_date="2025-01-01", candidates=candidates)

    entry = result[price_map_key("T1", "A", "B")]
    assert entry.failed is False
    assert entry.matched_by == "station_train_code"


async def test_on_leg_complete_invoked_for_fetched_and_cached_legs(
    redis: FakeRedis,
    station_repo: FakeStationRepo,
) -> None:
    client = FakeBatchTicketClient(default_rows=_make_rows("T1", "G1"))
    service = _build_service(redis, station_repo, ticket_client=client)
    callback = AsyncMock()
    candidates = [_candidate([_train_seg("T1", "G1", "A", "B")])]

    await service.prefetch_all_prices(
        run_date="2025-01-01",
        candidates=candidates,
        on_leg_complete=callback,
    )
    await service.prefetch_all_prices(
        run_date="2025-01-01",
        candidates=candidates,
        on_leg_complete=callback,
    )

    assert callback.await_count == 2
    batches = [call.args[0] for call in callback.await_args_list]
    assert all(
        isinstance(batch[price_map_key("T1", "A", "B")], PriceCacheEntry)
        for batch in batches
    )
