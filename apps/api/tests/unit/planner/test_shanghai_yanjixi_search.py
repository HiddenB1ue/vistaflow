from __future__ import annotations

import csv
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
        parts.append(
            f"{segment.train_code}/{segment.train_no} "
            f"{segment.from_station} {abs_min_to_hhmm(segment.depart_abs_min)} -> "
            f"{segment.to_station} {abs_min_to_hhmm(segment.arrive_abs_min)}"
        )
    total_minutes = route[-1].arrive_abs_min - route[0].depart_abs_min
    return f"{total_minutes // 60}h{total_minutes % 60:02d}m | " + " | ".join(parts)


def test_shanghai_to_yanjixi_on_may_1_with_three_transfers() -> None:
    """Exploratory seed-data search for 2026-05-01: Shanghai -> Yanji West, 3 transfers."""
    timetable = _load_seed_timetable()
    station_index = build_station_index(timetable)

    routes = search_journeys(
        from_stations={"上海"},
        to_stations={"延吉西"},
        transfer_values=[3],
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
        timetable=timetable,
        station_index=station_index,
    )
    ranked_routes = group_and_rank(routes, sort_by="duration", top_n_per_sequence=3)

    print(f"\nShanghai -> Yanji West, 2026-05-01, exactly 3 transfers: {len(ranked_routes)}")
    for index, route in enumerate(ranked_routes[:20], start=1):
        print(f"{index:02d}. {_format_route(route)}")

    assert all(len(route) == 4 for route in ranked_routes)
