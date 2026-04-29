from __future__ import annotations

import csv
import time
from pathlib import Path

from app.models import Segment, StopEvent, Timetable
from app.planner.index import build_station_index
from app.planner.ranking import group_and_rank
from app.planner.search import search_journeys
from app.planner.time_utils import abs_min_to_hhmm, advance_past, parse_hhmm


MINUTES_PER_DAY = 1440


def _seed_path() -> Path:
    return Path(__file__).resolve().parents[5] / "infra" / "sql" / "seeds" / "train_stops.csv"


def _abs_minutes(clock: str | None, day_diff: int) -> int | None:
    parsed = parse_hhmm(clock)
    if parsed is None:
        return None
    return day_diff * MINUTES_PER_DAY + parsed


def _load_seed_timetable() -> Timetable:
    rows_by_train: dict[str, list[dict[str, str]]] = {}
    with _seed_path().open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            train_no = (row.get("train_no") or "").strip()
            station_name = (row.get("station_name") or "").strip()
            if train_no and station_name:
                rows_by_train.setdefault(train_no, []).append(row)

    timetable: Timetable = {}
    for train_no, rows in rows_by_train.items():
        rows.sort(key=lambda item: int(item.get("station_no") or 0))
        total_stops = len(rows)
        previous_depart: int | None = None
        events: list[StopEvent] = []

        for row in rows:
            day_diff = int(row.get("arrive_day_diff") or 0)
            arrive_abs = _abs_minutes(row.get("arrive_time"), day_diff)
            depart_abs = _abs_minutes(row.get("start_time"), day_diff)

            if arrive_abs is None:
                arrive_abs = depart_abs
            if depart_abs is None:
                depart_abs = arrive_abs
            if arrive_abs is not None and depart_abs is not None:
                depart_abs = advance_past(depart_abs, arrive_abs)

            if previous_depart is not None:
                if arrive_abs is not None:
                    arrive_abs = advance_past(arrive_abs, previous_depart)
                if depart_abs is not None:
                    depart_abs = advance_past(depart_abs, previous_depart)

            if depart_abs is not None:
                previous_depart = depart_abs

            events.append(
                StopEvent(
                    train_no=train_no,
                    stop_number=int(row.get("station_no") or 0),
                    station_name=(row.get("station_name") or "").strip(),
                    train_code=(row.get("station_train_code") or "").strip(),
                    arrive_abs_min=arrive_abs,
                    depart_abs_min=depart_abs,
                    total_stops=total_stops,
                )
            )

        if len(events) >= 2:
            timetable[train_no] = events

    return timetable


def _format_route(route: list[Segment]) -> str:
    parts = []
    for segment in route:
        depart_day = segment.depart_abs_min // MINUTES_PER_DAY
        arrive_day = segment.arrive_abs_min // MINUTES_PER_DAY
        depart_label = f"+{depart_day} " if depart_day else ""
        arrive_label = f"+{arrive_day} " if arrive_day else ""
        parts.append(
            f"{segment.train_code}/{segment.train_no} "
            f"{segment.from_station} {depart_label}{abs_min_to_hhmm(segment.depart_abs_min)} -> "
            f"{segment.to_station} {arrive_label}{abs_min_to_hhmm(segment.arrive_abs_min)}"
        )
    total_minutes = route[-1].arrive_abs_min - route[0].depart_abs_min
    return f"{total_minutes // 60}h{total_minutes % 60:02d}m | " + " | ".join(parts)


def _search_exact_transfer_count(
    timetable: Timetable,
    transfer_count: int,
) -> tuple[list[list[Segment]], float, float]:
    station_index = build_station_index(timetable)

    start = time.perf_counter()
    routes = search_journeys(
        from_stations={"上海"},
        to_stations={"延吉西"},
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
        excluded_train_type_prefixes=set(),
        excluded_train_tokens=set(),
        allowed_train_tokens=set(),
        search_start_abs_min=0,
        first_departure_latest_abs_min=MINUTES_PER_DAY - 1,
        latest_arrival_abs_min=(3 * MINUTES_PER_DAY) - 1,
        timetable=timetable,
        station_index=station_index,
    )
    search_seconds = time.perf_counter() - start

    start = time.perf_counter()
    ranked_routes = group_and_rank(routes, sort_by="duration", top_n_per_sequence=0)
    rank_seconds = time.perf_counter() - start
    return ranked_routes, search_seconds, rank_seconds


def test_shanghai_to_yanjixi_on_may_1_print_top_10_by_transfer_count() -> None:
    """Print exploratory seed-data results for Shanghai -> Yanji West."""
    start = time.perf_counter()
    timetable = _load_seed_timetable()
    load_seconds = time.perf_counter() - start

    start = time.perf_counter()
    station_index = build_station_index(timetable)
    index_seconds = time.perf_counter() - start
    assert "上海" in station_index.departures_by_station
    assert "延吉西" in station_index.arrivals_by_station

    print(
        "\nShanghai -> Yanji West seed-data exploratory search "
        f"(trains={len(timetable)}, load={load_seconds:.3f}s, index={index_seconds:.3f}s)"
    )

    for transfer_count in (1, 2, 3):
        ranked_routes, search_seconds, rank_seconds = _search_exact_transfer_count(
            timetable,
            transfer_count,
        )
        print(
            f"\n=== transfers={transfer_count} "
            f"total={len(ranked_routes)} "
            f"search={search_seconds:.3f}s "
            f"rank={rank_seconds:.3f}s ==="
        )
        for index, route in enumerate(ranked_routes[:10], start=1):
            print(f"{index:02d}. {_format_route(route)}")

        assert all(len(route) == transfer_count + 1 for route in ranked_routes)
