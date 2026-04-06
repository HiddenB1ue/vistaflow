from __future__ import annotations

from typing import cast

from app.models import Segment, StopEvent, Timetable
from app.planner.index import build_station_index
from app.planner.search import search_journeys


def make_simple_timetable() -> Timetable:
    """北京南 → 上海虹桥直达 G1，以及一条换乘路线 G2 + G3。"""
    return {
        "G1": [
            StopEvent("G1", 1, "北京南", "G1", None, 480),
            StopEvent("G1", 2, "上海虹桥", "G1", 750, None),
        ],
        "G2": [
            StopEvent("G2", 1, "北京南", "G2", None, 500),
            StopEvent("G2", 2, "济南西", "G2", 600, 610),
        ],
        "G3": [
            StopEvent("G3", 1, "济南西", "G3", None, 660),
            StopEvent("G3", 2, "上海虹桥", "G3", 800, None),
        ],
    }


DEFAULT_PARAMS: dict[str, object] = {
    "from_stations": {"北京南"},
    "to_stations": {"上海虹桥"},
    "min_transfer_minutes": 30,
    "max_transfer_minutes": None,
    "arrival_deadline_abs_min": None,
    "departure_time_start_min": None,
    "departure_time_end_min": None,
    "departure_time_cross_day": False,
    "excluded_transfer_stations": set(),
    "allowed_transfer_stations": set(),
    "allowed_train_type_prefixes": (),
    "excluded_train_type_prefixes": set(),
    "excluded_train_tokens": set(),
    "allowed_train_tokens": set(),
}


def run_search(
    timetable: Timetable,
    transfer_count: int = 0,
    **overrides: object,
) -> list[list[Segment]]:
    index = build_station_index(timetable)
    return search_journeys(
        from_stations=cast(
            set[str],
            overrides.get("from_stations", DEFAULT_PARAMS["from_stations"]),
        ),
        to_stations=cast(
            set[str],
            overrides.get("to_stations", DEFAULT_PARAMS["to_stations"]),
        ),
        transfer_count=transfer_count,
        min_transfer_minutes=cast(
            int,
            overrides.get(
                "min_transfer_minutes",
                DEFAULT_PARAMS["min_transfer_minutes"],
            ),
        ),
        max_transfer_minutes=cast(
            int | None,
            overrides.get(
                "max_transfer_minutes",
                DEFAULT_PARAMS["max_transfer_minutes"],
            ),
        ),
        arrival_deadline_abs_min=cast(
            int | None,
            overrides.get(
                "arrival_deadline_abs_min",
                DEFAULT_PARAMS["arrival_deadline_abs_min"],
            ),
        ),
        departure_time_start_min=cast(
            int | None,
            overrides.get(
                "departure_time_start_min",
                DEFAULT_PARAMS["departure_time_start_min"],
            ),
        ),
        departure_time_end_min=cast(
            int | None,
            overrides.get(
                "departure_time_end_min",
                DEFAULT_PARAMS["departure_time_end_min"],
            ),
        ),
        departure_time_cross_day=cast(
            bool,
            overrides.get(
                "departure_time_cross_day",
                DEFAULT_PARAMS["departure_time_cross_day"],
            ),
        ),
        excluded_transfer_stations=cast(
            set[str],
            overrides.get(
                "excluded_transfer_stations",
                DEFAULT_PARAMS["excluded_transfer_stations"],
            ),
        ),
        allowed_transfer_stations=cast(
            set[str],
            overrides.get(
                "allowed_transfer_stations",
                DEFAULT_PARAMS["allowed_transfer_stations"],
            ),
        ),
        allowed_train_type_prefixes=cast(
            tuple[str, ...],
            overrides.get(
                "allowed_train_type_prefixes",
                DEFAULT_PARAMS["allowed_train_type_prefixes"],
            ),
        ),
        excluded_train_type_prefixes=cast(
            set[str],
            overrides.get(
                "excluded_train_type_prefixes",
                DEFAULT_PARAMS["excluded_train_type_prefixes"],
            ),
        ),
        excluded_train_tokens=cast(
            set[str],
            overrides.get(
                "excluded_train_tokens",
                DEFAULT_PARAMS["excluded_train_tokens"],
            ),
        ),
        allowed_train_tokens=cast(
            set[str],
            overrides.get(
                "allowed_train_tokens",
                DEFAULT_PARAMS["allowed_train_tokens"],
            ),
        ),
        timetable=timetable,
        station_index=index,
    )


def test_direct_route_found() -> None:
    results = run_search(make_simple_timetable(), transfer_count=0)
    assert len(results) == 1
    assert results[0][0].train_no == "G1"
    assert results[0][0].from_station == "北京南"
    assert results[0][0].to_station == "上海虹桥"


def test_no_route_when_no_train() -> None:
    timetable: Timetable = {
        "G1": [
            StopEvent("G1", 1, "北京南", "G1", None, 480),
            StopEvent("G1", 2, "济南西", "G1", 600, None),
        ]
    }
    results = run_search(timetable, transfer_count=0)
    assert results == []


def test_transfer_route_found() -> None:
    results = run_search(make_simple_timetable(), transfer_count=1)
    train_nos = {tuple(segment.train_no for segment in route) for route in results}
    assert ("G1",) in train_nos
    assert ("G2", "G3") in train_nos


def test_transfer_excluded_station() -> None:
    results = run_search(
        make_simple_timetable(),
        transfer_count=1,
        excluded_transfer_stations={"济南西"},
    )
    train_nos = {tuple(segment.train_no for segment in route) for route in results}
    assert ("G2", "G3") not in train_nos


def test_departure_time_filter() -> None:
    results = run_search(
        make_simple_timetable(),
        transfer_count=0,
        departure_time_start_min=540,
    )
    assert results == []


def test_allowed_train_type() -> None:
    results = run_search(
        make_simple_timetable(),
        transfer_count=0,
        allowed_train_type_prefixes=("D",),
    )
    assert results == []


def test_arrival_deadline() -> None:
    results = run_search(
        make_simple_timetable(),
        transfer_count=0,
        arrival_deadline_abs_min=700,
    )
    assert results == []
