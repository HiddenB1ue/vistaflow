from __future__ import annotations

from typing import Literal

from app.models import Segment
from app.planner.filters import get_train_type


def route_duration(route: list[Segment]) -> int:
    """计算路线总耗时（分钟）。"""
    return route[-1].arrive_abs_min - route[0].depart_abs_min


def route_sort_key(
    route: list[Segment],
    sort_by: Literal["duration", "departure"],
) -> tuple[int, float, int, int, int]:
    """生成路线排序键，优先级：换乘次数 → 主排序字段 → 总耗时 → 出发时间 → 到达时间。"""
    transfers = len(route) - 1
    duration = route_duration(route)
    departure = route[0].depart_abs_min
    arrival = route[-1].arrive_abs_min

    if sort_by == "departure":
        primary = float(departure)
    else:
        primary = float(duration)

    return (transfers, primary, duration, departure, arrival)


def route_train_signature(route: list[Segment]) -> tuple[str, ...]:
    """生成路线的列车序列签名，用于分组去重。"""
    return tuple(seg.train_no for seg in route)


def group_and_rank(
    routes: list[list[Segment]],
    sort_by: Literal["duration", "departure"] = "duration",
    top_n_per_sequence: int = 1,
) -> list[list[Segment]]:
    """按列车序列分组，每组保留 top_n 个方案，再按排序键整体排序。

    top_n_per_sequence=0 表示每组保留所有方案。
    """
    grouped: dict[tuple[str, ...], list[list[Segment]]] = {}
    for route in routes:
        sig = route_train_signature(route)
        grouped.setdefault(sig, []).append(route)

    result: list[list[Segment]] = []
    for candidates in grouped.values():
        candidates.sort(key=lambda r: route_sort_key(r, sort_by))
        kept = candidates if top_n_per_sequence == 0 else candidates[:top_n_per_sequence]
        result.extend(kept)

    result.sort(key=lambda r: route_sort_key(r, sort_by))
    return result


def apply_display_limit(routes: list[list[Segment]], limit: int) -> list[list[Segment]]:
    """截取前 limit 条方案，limit <= 0 表示不限制。"""
    if limit <= 0:
        return routes
    return routes[:limit]



def exclude_direct_train_codes_in_transfer_routes(
    routes: list[list[Segment]],
    enabled: bool,
) -> list[list[Segment]]:
    """排除在换乘方案中使用直达车次代码的路线。"""
    if not enabled:
        return routes

    direct_train_codes = {
        route[0].train_code.upper()
        for route in routes
        if len(route) == 1
    }

    if not direct_train_codes:
        return routes

    return [
        route
        for route in routes
        if len(route) == 1
        or all(
            segment.train_code.upper() not in direct_train_codes
            for segment in route
        )
    ]


def filter_routes_by_display_train_types(
    routes: list[list[Segment]],
    display_train_type_prefixes: set[str],
) -> list[list[Segment]]:
    """仅保留所有 Segment 都属于指定车型的路线。"""
    if not display_train_type_prefixes:
        return routes

    return [
        route
        for route in routes
        if all(
            get_train_type(segment.train_code) in display_train_type_prefixes
            for segment in route
        )
    ]
