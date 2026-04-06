from __future__ import annotations

from app.models import SeatInfo, SeatLookupKey, Segment
from app.planner.ranking import (
    apply_display_limit,
    group_and_rank,
    route_duration,
    route_min_price,
)


def seg(train_no: str, depart: int, arrive: int, from_s: str = "A", to_s: str = "B") -> Segment:
    return Segment(
        train_no=train_no,
        train_code=train_no,
        from_station=from_s,
        to_station=to_s,
        depart_abs_min=depart,
        arrive_abs_min=arrive,
    )


def test_route_duration() -> None:
    route = [seg("G1", 480, 750)]
    assert route_duration(route) == 270


def test_route_min_price_with_data() -> None:
    route = [seg("G1", 480, 750, "北京南", "上海虹桥")]
    seat_data: dict[SeatLookupKey, list[SeatInfo]] = {
        ("G1", "北京南", "上海虹桥"): [
            SeatInfo(seat_type="ze", status="有", price=553.0, available=True),
            SeatInfo(seat_type="zy", status="有", price=933.0, available=True),
        ]
    }
    assert route_min_price(route, seat_data) == 553.0


def test_route_min_price_no_data() -> None:
    route = [seg("G1", 480, 750, "北京南", "上海虹桥")]
    assert route_min_price(route, {}) is None


def test_group_and_rank_by_duration() -> None:
    routes = [
        [seg("G2", 500, 800)],  # 300 min
        [seg("G1", 480, 750)],  # 270 min — 更短
    ]
    ranked = group_and_rank(routes, sort_by="duration")
    assert ranked[0][0].train_no == "G1"


def test_group_and_rank_dedup_same_sequence() -> None:
    """相同列车序列只保留最优一条。"""
    routes = [
        [seg("G1", 480, 760)],  # 280 min
        [seg("G1", 480, 750)],  # 270 min — 更短，应保留
    ]
    ranked = group_and_rank(routes, sort_by="duration", top_n_per_sequence=1)
    assert len(ranked) == 1
    assert ranked[0][0].arrive_abs_min == 750


def test_apply_display_limit() -> None:
    routes = [[seg(f"G{i}", 480, 750)] for i in range(10)]
    assert len(apply_display_limit(routes, 3)) == 3
    assert len(apply_display_limit(routes, 0)) == 10
