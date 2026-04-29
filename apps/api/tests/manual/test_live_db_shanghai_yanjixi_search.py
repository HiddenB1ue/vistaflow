from __future__ import annotations

import os
from datetime import date, timedelta

import asyncpg
import pytest

from app.models import Segment
from app.planner.index import build_station_index
from app.planner.ranking import group_and_rank
from app.planner.search import search_journeys
from app.planner.time_utils import abs_min_to_hhmm
from app.railway.repository import TimetableRepository

MINUTES_PER_DAY = 1440
SEARCH_DATE = "2026-05-01"
FROM_STATION = "上海"
TO_STATION = "长春"

RUN_LIVE_DB_TESTS = os.getenv("RUN_LIVE_DB_TESTS") == "1"

LIVE_DB_TEST_SKIP_MARK = pytest.mark.skipif(
    not RUN_LIVE_DB_TESTS,
    reason="manual live DB test is disabled by default; set RUN_LIVE_DB_TESTS=1 to enable",
)


class _ConnectionAcquireContext:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def __aenter__(self) -> asyncpg.Connection:
        return self._conn

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class _SingleConnectionPool:
    """Tiny pool adapter that bypasses tests/conftest.py mocking asyncpg.create_pool."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    def acquire(self) -> _ConnectionAcquireContext:
        return _ConnectionAcquireContext(self._conn)

    async def close(self) -> None:
        await self._conn.close()


def _database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url or database_url == "postgresql://test":
        raise AssertionError("set DATABASE_URL to a real VistaFlow PostgreSQL database")
    return database_url


def _filter_running_only() -> bool:
    return os.getenv("LIVE_DB_FILTER_RUNNING_ONLY", "1") != "0"


def _date_for_abs_min(search_date: str, abs_min: int) -> str:
    return (
        date.fromisoformat(search_date) + timedelta(days=abs_min // MINUTES_PER_DAY)
    ).isoformat()


def _format_route(route: list[Segment]) -> str:
    parts = []
    for segment in route:
        depart_day = segment.depart_abs_min // MINUTES_PER_DAY
        arrive_day = segment.arrive_abs_min // MINUTES_PER_DAY
        depart_label = f"+{depart_day}日 " if depart_day else ""
        arrive_label = f"+{arrive_day}日 " if arrive_day else ""
        parts.append(
            f"{segment.train_code}/{segment.train_no} "
            f"{segment.from_station} {depart_label}{abs_min_to_hhmm(segment.depart_abs_min)} 到 "
            f"{segment.to_station} {arrive_label}{abs_min_to_hhmm(segment.arrive_abs_min)}"
        )
    total_minutes = route[-1].arrive_abs_min - route[0].depart_abs_min
    return f"{total_minutes // 60}小时{total_minutes % 60:02d}分钟 | " + " | ".join(parts)


def _print_route_summary(
    transfer_count: int,
    ranked_routes: list[list[Segment]],
) -> None:
    print(f"\n中转 {transfer_count} 次：方案数 {len(ranked_routes)}")
    for index, route in enumerate(ranked_routes[:5], start=1):
        print(f"{index:02d}. {_format_route(route)}")


def _fare_segment_key(segment: Segment) -> tuple[str, str, str, str, str]:
    return (
        _date_for_abs_min(SEARCH_DATE, segment.depart_abs_min),
        segment.train_no,
        segment.train_code,
        segment.from_station,
        segment.to_station,
    )


def _fare_segment_keys(routes: list[list[Segment]]) -> set[tuple[str, str, str, str, str]]:
    return {_fare_segment_key(segment) for route in routes for segment in route}


@LIVE_DB_TEST_SKIP_MARK
@pytest.mark.asyncio
async def test_live_db_shanghai_to_yanjixi_on_may_1_print_top_10_by_transfer_count() -> None:
    conn = await asyncpg.connect(dsn=_database_url())
    pool = _SingleConnectionPool(conn)
    try:
        repo = TimetableRepository(pool)
        filter_running_only = _filter_running_only()

        timetable = await repo.load_timetable(SEARCH_DATE, filter_running_only=filter_running_only)

        station_index = build_station_index(timetable)

        assert timetable, (
            "loaded timetable is empty; with LIVE_DB_FILTER_RUNNING_ONLY=1 this usually means "
            "there are no running train_runs in 2026-04-28..2026-05-03. "
            "Populate train_runs for that window, or rerun with LIVE_DB_FILTER_RUNNING_ONLY=0 "
            "to benchmark against train_stops only."
        )
        assert FROM_STATION in station_index.departures_by_station
        assert TO_STATION in station_index.arrivals_by_station

        routes_by_transfer_count: dict[int, list[list[Segment]]] = {}
        fare_segments_by_transfer_count: dict[int, set[tuple[str, str, str, str, str]]] = {}
        all_route_fare_segments: set[tuple[str, str, str, str, str]] = set()

        for transfer_count in (1, 2, 3):
            routes = search_journeys(
                from_stations={FROM_STATION},
                to_stations={TO_STATION},
                transfer_values=[transfer_count],
                min_transfer_minutes=30,
                max_transfer_minutes=None,
                arrival_deadline_abs_min=None,
                departure_time_start_min=None,
                departure_time_end_min=None,
                departure_time_cross_day=False,
                excluded_transfer_stations=set(),
                allowed_transfer_stations=set(),
                allowed_train_type_prefixes=(),
                excluded_train_type_prefixes={"G", "C","Z"},
                excluded_train_tokens=set(),
                allowed_train_tokens=set(),
                search_start_abs_min=0,
                first_departure_latest_abs_min=MINUTES_PER_DAY - 1,
                latest_arrival_abs_min=(3 * MINUTES_PER_DAY) - 1,
                timetable=timetable,
                station_index=station_index,
            )

            ranked_routes = group_and_rank(routes, sort_by="duration", top_n_per_sequence=0)

            current_all_keys = _fare_segment_keys(ranked_routes)
            routes_by_transfer_count[transfer_count] = ranked_routes
            fare_segments_by_transfer_count[transfer_count] = current_all_keys
            all_route_fare_segments.update(current_all_keys)

            assert all(len(route) == transfer_count + 1 for route in ranked_routes)

        print(f"\n方案统计：{FROM_STATION} 到 {TO_STATION}，出发日期 {SEARCH_DATE}")
        total_routes = 0
        for transfer_count in (1, 2, 3):
            ranked_routes = routes_by_transfer_count[transfer_count]
            total_routes += len(ranked_routes)
            _print_route_summary(transfer_count, ranked_routes)
        print(f"\n总方案数：{total_routes}")

        print("\n唯一区段统计：")
        for transfer_count in (1, 2, 3):
            keys = fare_segments_by_transfer_count[transfer_count]
            print(f"中转 {transfer_count} 次：唯一区段数 {len(keys)}")
        print(f"汇总唯一区段数：{len(all_route_fare_segments)}")
    finally:
        await pool.close()
