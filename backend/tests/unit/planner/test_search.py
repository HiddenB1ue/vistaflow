from __future__ import annotations

from app.domain.models import StopEvent
from app.domain.types import Timetable
from app.planner.index import build_station_index
from app.planner.search import search_journeys


def make_simple_timetable() -> Timetable:
    """北京南 → 上海虹桥 直达 G1，以及一条换乘路线 G2(北京南→济南西) + G3(济南西→上海虹桥)。"""
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


DEFAULT_PARAMS: dict = dict(
    from_stations={"北京南"},
    to_stations={"上海虹桥"},
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
)


def run_search(timetable: Timetable, transfer_count: int = 0, **overrides) -> list:
    index = build_station_index(timetable)
    params = {**DEFAULT_PARAMS, **overrides, "transfer_count": transfer_count,
              "timetable": timetable, "station_index": index}
    return search_journeys(**params)


# --- 直达 ---

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


# --- 换乘 ---

def test_transfer_route_found() -> None:
    results = run_search(make_simple_timetable(), transfer_count=1)
    train_nos = {tuple(s.train_no for s in r) for r in results}
    assert ("G1",) in train_nos          # 直达也包含
    assert ("G2", "G3") in train_nos     # 换乘方案


def test_transfer_excluded_station() -> None:
    """排除济南西作为换乘站，换乘方案应消失。"""
    results = run_search(
        make_simple_timetable(),
        transfer_count=1,
        excluded_transfer_stations={"济南西"},
    )
    train_nos = {tuple(s.train_no for s in r) for r in results}
    assert ("G2", "G3") not in train_nos


# --- 时间过滤 ---

def test_departure_time_filter() -> None:
    """G1 出发 08:00(480min)，若要求 09:00 以后出发，应找不到。"""
    results = run_search(
        make_simple_timetable(),
        transfer_count=0,
        departure_time_start_min=540,  # 09:00
    )
    assert results == []


# --- 车型过滤 ---

def test_allowed_train_type() -> None:
    """只允许 D 字头，G1 应被过滤掉。"""
    results = run_search(
        make_simple_timetable(),
        transfer_count=0,
        allowed_train_type_prefixes=("D",),
    )
    assert results == []


# --- 到达时限 ---

def test_arrival_deadline() -> None:
    """G1 到达 12:30(750min)，若截止时间为 700，应找不到。"""
    results = run_search(
        make_simple_timetable(),
        transfer_count=0,
        arrival_deadline_abs_min=700,
    )
    assert results == []
