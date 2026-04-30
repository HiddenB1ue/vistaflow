from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from app.journey_search_sessions.schemas import (
    CachedRouteCandidate,
    CachedTrainSegment,
    RoutePointResponse,
    RouteStationResponse,
    RouteTransferSegmentResponse,
)
from app.route_plan_cache.repository import (
    RoutePlanQueryFilters,
    RoutePlanRepository,
    RoutePlanViewQuery,
)

REPO_ROOT = Path(__file__).resolve().parents[5]


def _station(name: str) -> RouteStationResponse:
    return RouteStationResponse(name=name, lng=1.0, lat=2.0)


def test_route_plan_segment_uses_plan_level_foreign_key() -> None:
    migration_sql = (
        REPO_ROOT / "infra/sql/migrations/0013_route_plan_cache.sql"
    ).read_text(encoding="utf-8")

    assert "REFERENCES route_plan_cache(plan_id) ON DELETE CASCADE" in migration_sql
    assert "REFERENCES route_plan_candidate(plan_id, route_id)" not in migration_sql


def test_route_plan_cache_does_not_use_expires_at() -> None:
    migration_sql = (
        REPO_ROOT / "infra/sql/migrations/0013_route_plan_cache.sql"
    ).read_text(encoding="utf-8")

    assert "expires_at" not in migration_sql
    assert "idx_route_plan_cache_status_expires" not in migration_sql


def test_candidate_and_segment_rows_round_trip() -> None:
    repo = RoutePlanRepository(pool=None)  # type: ignore[arg-type]
    plan_id = UUID("00000000-0000-0000-0000-000000000001")
    candidate = CachedRouteCandidate(
        id="route-1",
        trainNo="G1 / D11",
        type="中转 1 次",
        origin=_station("Beijing South"),
        destination=_station("Shanghai Hongqiao"),
        departureDate="2026-04-15",
        departureTime="07:30",
        arrivalDate="2026-04-16",
        arrivalTime="10:30",
        durationMinutes=180,
        segs=[
            CachedTrainSegment(
                trainNo="240000G1010A",
                no="G1",
                origin=_station("Beijing South"),
                destination=_station("Jinan West"),
                departureDate="2026-04-15",
                departureTime="07:30",
                arrivalDate="2026-04-15",
                arrivalTime="08:30",
                stopsCount=1,
            ),
            RouteTransferSegmentResponse(transfer="Jinan West 换乘 D11"),
            CachedTrainSegment(
                trainNo="240000D1100B",
                no="D11",
                origin=_station("Jinan West"),
                destination=_station("Shanghai Hongqiao"),
                departureDate="2026-04-16",
                departureTime="09:00",
                arrivalDate="2026-04-16",
                arrivalTime="10:30",
                stopsCount=2,
            ),
        ],
        pathPoints=[RoutePointResponse(lng=1.0, lat=2.0)],
        isDirect=False,
        transferCount=1,
        trainTypes=["D", "G"],
        trainCodes=["G1", "D11"],
    )

    candidate_row = repo._candidate_row(plan_id, candidate, date(2026, 4, 15), 1, 1)
    segment_rows = [
        repo._segment_row(plan_id, candidate, segment, date(2026, 4, 15), index)
        for index, segment in enumerate(
            segment
            for segment in candidate.segs
            if isinstance(segment, CachedTrainSegment)
        )
    ]

    assert candidate_row[0] == plan_id
    assert candidate_row[1] == "route-1"
    assert candidate_row[2] == 1
    assert candidate_row[22] == 1470
    assert candidate_row[23] == 1470
    assert candidate_row[24] == 1470
    assert len(segment_rows) == 2
    assert segment_rows[0][2] == 0
    assert segment_rows[1][2] == 1


class FakeAcquire:
    def __init__(self, conn: FakeConnection) -> None:
        self._conn = conn

    async def __aenter__(self) -> FakeConnection:
        return self._conn

    async def __aexit__(self, *_args: object) -> None:
        return None


class FakePool:
    def __init__(self, conn: FakeConnection) -> None:
        self._conn = conn

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self._conn)


class FakeRow(dict[str, Any]):
    def __getitem__(self, key: str) -> Any:
        return super().__getitem__(key)


class FakeConnection:
    def __init__(self) -> None:
        self.fetch_calls: list[tuple[str, tuple[object, ...]]] = []
        self.fetchrow_calls: list[tuple[str, tuple[object, ...]]] = []
        self.plan_id = UUID("00000000-0000-0000-0000-000000000001")

    async def fetch(self, sql: str, *params: object) -> list[FakeRow]:
        self.fetch_calls.append((sql, params))
        if "SELECT DISTINCT transfer_count" in sql:
            return [FakeRow(transfer_count=0)]
        if "SELECT DISTINCT unnest(train_types)" in sql:
            return [FakeRow(train_type="G")]
        if "SELECT DISTINCT unnest(train_codes)" in sql:
            return [FakeRow(train_code="G1")]
        if "FROM route_plan_candidate" in sql:
            return [
                FakeRow(
                    plan_id=self.plan_id,
                    route_id="paged-route",
                    transfer_count=0,
                    is_direct=True,
                    origin_station_snapshot={"name": "A", "lng": 1.0, "lat": 2.0},
                    destination_station_snapshot={"name": "B", "lng": 3.0, "lat": 4.0},
                    path_points=[],
                    train_no_label="G1",
                    route_type="直达",
                    departure_date=date(2026, 4, 15),
                    departure_time="08:00",
                    arrival_date=date(2026, 4, 15),
                    arrival_time="10:00",
                    duration_minutes=120,
                    train_codes=["G1"],
                    train_nos=["240000G1010A"],
                    train_types=["G"],
                )
            ]
        if "FROM route_plan_segment" in sql:
            return [
                FakeRow(
                    plan_id=self.plan_id,
                    route_id="paged-route",
                    segment_index=0,
                    train_no="240000G1010A",
                    train_code="G1",
                    origin_station_snapshot={"name": "A", "lng": 1.0, "lat": 2.0},
                    destination_station_snapshot={"name": "B", "lng": 3.0, "lat": 4.0},
                    departure_date=date(2026, 4, 15),
                    departure_time="08:00",
                    arrival_date=date(2026, 4, 15),
                    arrival_time="10:00",
                    stops_count=2,
                )
            ]
        return []

    async def fetchrow(self, sql: str, *params: object) -> FakeRow:
        self.fetchrow_calls.append((sql, params))
        return FakeRow(total=25)


@pytest.mark.asyncio
async def test_query_view_fetches_segments_only_for_paged_candidates() -> None:
    conn = FakeConnection()
    repo = RoutePlanRepository(pool=FakePool(conn))  # type: ignore[arg-type]
    plan_id = "00000000-0000-0000-0000-000000000001"

    result = await repo.query_view(
        [plan_id],
        RoutePlanViewQuery(
            filters=RoutePlanQueryFilters(),
            sort_by="duration",
            page=2,
            page_size=1,
        ),
    )

    segment_call = next(
        params
        for sql, params in conn.fetch_calls
        if "FROM route_plan_segment" in sql
    )
    assert result.total == 25
    assert [candidate.id for candidate in result.candidates] == ["paged-route"]
    assert segment_call[0] == [UUID(plan_id)]
    assert segment_call[1] == ["paged-route"]
