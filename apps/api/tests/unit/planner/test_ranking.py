from __future__ import annotations

from app.models import Segment
from app.planner.ranking import apply_display_limit, group_and_rank, route_duration


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


def test_group_and_rank_prefers_fewer_transfers_before_departure() -> None:
    routes = [
        [seg("G1", 480, 750)],
        [seg("G2", 450, 520), seg("D3", 540, 600, "B", "C")],
    ]
    ranked = group_and_rank(routes, sort_by="departure")
    assert len(ranked[0]) == 1
    assert ranked[0][0].train_no == "G1"


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
