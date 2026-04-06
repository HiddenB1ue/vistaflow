from __future__ import annotations

from typing import Literal

from app.models import SeatInfo, SeatLookupKey, Segment


def route_duration(route: list[Segment]) -> int:
    """计算路线总耗时（分钟）。"""
    return route[-1].arrive_abs_min - route[0].depart_abs_min


def route_min_price(
    route: list[Segment],
    seat_data: dict[SeatLookupKey, list[SeatInfo]],
) -> float | None:
    """计算路线各段最低价格之和。任意一段无价格数据则返回 None。"""
    total = 0.0
    for seg in route:
        key: SeatLookupKey = (seg.train_no, seg.from_station, seg.to_station)
        seats = seat_data.get(key, [])
        prices = [s.price for s in seats if s.price is not None and s.available]
        if not prices:
            return None
        total += min(prices)
    return total


def route_sort_key(
    route: list[Segment],
    sort_by: Literal["duration", "price", "departure"],
    seat_data: dict[SeatLookupKey, list[SeatInfo]] | None,
) -> tuple[int, float, int, int]:
    """生成路线排序键，优先级：换乘次数 → 主排序字段 → 总耗时 → 出发时间。"""
    transfers = len(route) - 1
    duration = route_duration(route)
    departure = route[0].depart_abs_min

    if sort_by == "price" and seat_data:
        price = route_min_price(route, seat_data)
        primary = price if price is not None else float("inf")
    elif sort_by == "departure":
        primary = float(departure)
    else:  # duration（默认）
        primary = float(duration)

    return (transfers, primary, duration, departure)


def route_train_signature(route: list[Segment]) -> tuple[str, ...]:
    """生成路线的列车序列签名，用于分组去重。"""
    return tuple(seg.train_no for seg in route)


def group_and_rank(
    routes: list[list[Segment]],
    sort_by: Literal["duration", "price", "departure"] = "duration",
    top_n_per_sequence: int = 1,
    seat_data: dict[SeatLookupKey, list[SeatInfo]] | None = None,
) -> list[list[Segment]]:
    """按列车序列分组，每组保留 top_n 个方案，再按排序键整体排序。

    top_n_per_sequence=0 表示每组保留所有方案。
    """
    _seat_data = seat_data or {}

    grouped: dict[tuple[str, ...], list[list[Segment]]] = {}
    for route in routes:
        sig = route_train_signature(route)
        grouped.setdefault(sig, []).append(route)

    result: list[list[Segment]] = []
    for candidates in grouped.values():
        candidates.sort(key=lambda r: route_sort_key(r, sort_by, _seat_data))
        kept = candidates if top_n_per_sequence == 0 else candidates[:top_n_per_sequence]
        result.extend(kept)

    result.sort(key=lambda r: route_sort_key(r, sort_by, _seat_data))
    return result


def apply_display_limit(routes: list[list[Segment]], limit: int) -> list[list[Segment]]:
    """截取前 limit 条方案，limit <= 0 表示不限制。"""
    if limit <= 0:
        return routes
    return routes[:limit]
