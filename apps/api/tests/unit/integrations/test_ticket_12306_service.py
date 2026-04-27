from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.integrations.ticket_12306.models import TicketSegmentData
from app.integrations.ticket_12306.service import Ticket12306Service
from app.journey_search_sessions.schemas import (
    CachedRouteCandidate,
    CachedTrainSegment,
    PriceCacheEntry,
    RoutePointResponse,
    RouteStationResponse,
    RouteTransferSegmentResponse,
    price_map_key,
)
from app.models import SeatInfo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _station(name: str, code: str = "") -> RouteStationResponse:
    return RouteStationResponse(name=name, code=code, city="", lng=0.0, lat=0.0)


def _train_seg(
    train_no: str,
    no: str,
    origin_name: str,
    dest_name: str,
) -> CachedTrainSegment:
    return CachedTrainSegment(
        trainNo=train_no,
        no=no,
        origin=_station(origin_name),
        destination=_station(dest_name),
        departureTime="08:00",
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
        departureTime="08:00",
        arrivalTime="10:00",
        durationMinutes=120,
        segs=segs,
        pathPoints=[],
        isDirect=True,
        transferCount=0,
    )


class FakeRedis:
    """Minimal async Redis stub for testing."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def mget(self, keys: list[str]) -> list[str | None]:
        return [self._store.get(k) for k in keys]

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        self._store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)


class FakeStationRepo:
    """Stub that maps station names to telecodes."""

    def __init__(self, telecodes: dict[str, str]) -> None:
        self._telecodes = telecodes

    async def get_telecodes_by_names(self, names: set[str]) -> dict[str, str]:
        return {n: self._telecodes[n] for n in names if n in self._telecodes}


def _make_fetch_leg_rows(
    train_no: str,
    stc: str,
    seat_status: dict[str, str] | None = None,
    seat_prices: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build a rows dict as returned by fetch_leg."""
    ss = seat_status or {"ze": "有", "zy": "有"}
    sp = seat_prices or {"ze": 55.5, "zy": 99.0}
    entry = (ss, sp)
    rows: dict[str, Any] = {}
    if train_no:
        rows[train_no] = entry
    if stc:
        rows[stc] = entry
    return rows


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPrefetchAllPrices:
    """Unit tests for Ticket12306Service.prefetch_all_prices."""

    @pytest.fixture
    def redis(self) -> FakeRedis:
        return FakeRedis()

    @pytest.fixture
    def station_repo(self) -> FakeStationRepo:
        return FakeStationRepo({
            "北京": "BJP",
            "上海": "SHH",
            "南京": "NJH",
            "杭州": "HZH",
        })

    def _build_service(
        self,
        redis: FakeRedis,
        station_repo: FakeStationRepo,
        ticket_client: Any = None,
    ) -> Ticket12306Service:
        return Ticket12306Service(
            redis_client=redis,  # type: ignore[arg-type]
            station_repo=station_repo,  # type: ignore[arg-type]
            ticket_client=ticket_client,
            cache_ttl_seconds=60,
            failure_ttl_seconds=10,
        )

    # --- Req 1.4: ticket_client is None → return empty dict ---
    async def test_returns_empty_when_no_ticket_client(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        service = self._build_service(redis, station_repo, ticket_client=None)
        candidates = [_candidate([_train_seg("T1", "G1", "北京", "上海")])]
        result = await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=candidates
        )
        assert result == {}

    # --- Basic success path ---
    async def test_basic_prefetch_returns_price_map(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()
        mock_client.fetch_leg.return_value = _make_fetch_leg_rows("T1", "G1")

        service = self._build_service(redis, station_repo, ticket_client=mock_client)
        candidates = [_candidate([_train_seg("T1", "G1", "北京", "上海")])]

        result = await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=candidates
        )

        key = price_map_key("T1", "北京", "上海")
        assert key in result
        entry = result[key]
        assert isinstance(entry, PriceCacheEntry)
        assert entry.failed is False
        assert entry.min_price is not None
        assert len(entry.seats) > 0

    # --- Req 1.3: Leg deduplication ---
    async def test_deduplicates_legs(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()
        mock_client.fetch_leg.return_value = _make_fetch_leg_rows("T1", "G1")

        service = self._build_service(redis, station_repo, ticket_client=mock_client)
        # Two candidates with same leg (北京→上海) but different trains
        seg1 = _train_seg("T1", "G1", "北京", "上海")
        seg2 = _train_seg("T2", "G2", "北京", "上海")
        # Add T2 to the fetch_leg return
        rows = _make_fetch_leg_rows("T1", "G1")
        rows["T2"] = rows["T1"]
        rows["G2"] = rows["T1"]
        mock_client.fetch_leg.return_value = rows

        candidates = [_candidate([seg1], "c1"), _candidate([seg2], "c2")]
        await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=candidates
        )

        # Only one fetch_leg call since both segments share the same leg
        assert mock_client.fetch_leg.call_count == 1

    # --- Req 1.5: Partial failure resilience ---
    async def test_partial_failure_does_not_raise(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()

        # Use side_effect function to control which leg fails based on args
        async def _fetch_leg(
            run_date: str,
            from_station: str,
            to_station: str,
            from_code: str,
            to_code: str,
        ) -> dict[str, Any]:
            if to_code == "SHH":
                return _make_fetch_leg_rows("T1", "G1")
            raise Exception("network error")

        mock_client.fetch_leg.side_effect = _fetch_leg

        service = self._build_service(redis, station_repo, ticket_client=mock_client)
        seg1 = _train_seg("T1", "G1", "北京", "上海")
        seg2 = _train_seg("T2", "G2", "北京", "南京")

        candidates = [_candidate([seg1], "c1"), _candidate([seg2], "c2")]
        result = await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=candidates
        )

        # First segment should succeed
        key1 = price_map_key("T1", "北京", "上海")
        assert key1 in result
        assert result[key1].failed is False

        # Second segment should be marked as failed
        key2 = price_map_key("T2", "北京", "南京")
        assert key2 in result
        assert result[key2].failed is True

    # --- Req 3.1, 3.2: Cache hit → no HTTP call ---
    async def test_cache_hit_skips_fetch(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()
        service = self._build_service(redis, station_repo, ticket_client=mock_client)

        # Pre-populate Redis cache
        cache_key = "journey_search:ticket_segment:2025-01-01:T1:BJP:SHH"
        cache_payload = {
            "ok": True,
            "data": {
                "seats": [
                    {"seat_type": "ze", "status": "有", "price": 55.5, "available": True}
                ],
                "min_price": 55.5,
                "matched_by": "train_no",
            },
        }
        redis._store[cache_key] = json.dumps(cache_payload)

        candidates = [_candidate([_train_seg("T1", "G1", "北京", "上海")])]
        result = await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=candidates
        )

        # Should not call fetch_leg since cache hit
        mock_client.fetch_leg.assert_not_called()

        key = price_map_key("T1", "北京", "上海")
        assert key in result
        assert result[key].failed is False
        assert result[key].min_price == 55.5

    # --- Req 3.3: Cache miss + success → result written to cache ---
    async def test_cache_miss_stores_result(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()
        mock_client.fetch_leg.return_value = _make_fetch_leg_rows("T1", "G1")

        service = self._build_service(redis, station_repo, ticket_client=mock_client)
        candidates = [_candidate([_train_seg("T1", "G1", "北京", "上海")])]

        await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=candidates
        )

        cache_key = "journey_search:ticket_segment:2025-01-01:T1:BJP:SHH"
        raw = redis._store.get(cache_key)
        assert raw is not None
        payload = json.loads(raw)
        assert payload["ok"] is True

    # --- Req 3.4: Cache miss + failure → failure marker written ---
    async def test_cache_miss_failure_stores_failure_marker(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()
        mock_client.fetch_leg.side_effect = Exception("timeout")

        service = self._build_service(redis, station_repo, ticket_client=mock_client)
        candidates = [_candidate([_train_seg("T1", "G1", "北京", "上海")])]

        result = await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=candidates
        )

        cache_key = "journey_search:ticket_segment:2025-01-01:T1:BJP:SHH"
        raw = redis._store.get(cache_key)
        assert raw is not None
        payload = json.loads(raw)
        assert payload["ok"] is False

        key = price_map_key("T1", "北京", "上海")
        assert result[key].failed is True

    # --- Req 2.2: Default max concurrency is 5 ---
    async def test_default_max_concurrency(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()
        mock_client.fetch_leg.return_value = {}

        service = self._build_service(redis, station_repo, ticket_client=mock_client)
        candidates = [_candidate([_train_seg("T1", "G1", "北京", "上海")])]

        # Just verify it runs without error with default concurrency
        import inspect
        sig = inspect.signature(service.prefetch_all_prices)
        assert sig.parameters["max_concurrency"].default == 5

    # --- Transfer segments are skipped ---
    async def test_skips_transfer_segments(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()
        mock_client.fetch_leg.return_value = _make_fetch_leg_rows("T1", "G1")

        service = self._build_service(redis, station_repo, ticket_client=mock_client)
        segs: list[CachedTrainSegment | RouteTransferSegmentResponse] = [
            _train_seg("T1", "G1", "北京", "南京"),
            RouteTransferSegmentResponse(transfer="南京"),
            _train_seg("T2", "G2", "南京", "上海"),
        ]
        # Add T2 rows for the second leg
        rows2 = _make_fetch_leg_rows("T2", "G2")
        mock_client.fetch_leg.side_effect = [
            _make_fetch_leg_rows("T1", "G1"),
            rows2,
        ]

        candidates = [_candidate(segs)]
        result = await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=candidates
        )

        # Should have entries for both train segments but not the transfer
        key1 = price_map_key("T1", "北京", "南京")
        key2 = price_map_key("T2", "南京", "上海")
        assert key1 in result
        assert key2 in result
        assert len(result) == 2

    # --- Empty candidates → empty result ---
    async def test_empty_candidates_returns_empty(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()
        service = self._build_service(redis, station_repo, ticket_client=mock_client)
        result = await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=[]
        )
        assert result == {}

    # --- station_train_code fallback matching ---
    async def test_matches_by_station_train_code_fallback(
        self, redis: FakeRedis, station_repo: FakeStationRepo
    ) -> None:
        mock_client = AsyncMock()
        # Only return data keyed by station_train_code, not train_no
        mock_client.fetch_leg.return_value = {"G1": ({"ze": "有"}, {"ze": 55.5})}

        service = self._build_service(redis, station_repo, ticket_client=mock_client)
        candidates = [_candidate([_train_seg("T1", "G1", "北京", "上海")])]

        result = await service.prefetch_all_prices(
            run_date="2025-01-01", candidates=candidates
        )

        key = price_map_key("T1", "北京", "上海")
        assert key in result
        assert result[key].matched_by == "station_train_code"
        assert result[key].failed is False
