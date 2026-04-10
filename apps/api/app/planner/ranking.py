from __future__ import annotations

from typing import Literal

from app.models import SeatInfo, SeatLookupKey, Segment
from app.planner.filters import get_train_type


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
) -> tuple[int, float, int, int, int]:
    """生成路线排序键，优先级：换乘次数 → 主排序字段 → 总耗时 → 出发时间 → 到达时间。
    
    Args:
        route: 路线（Segment 列表）
        sort_by: 排序字段（"duration", "price", "departure"）
        seat_data: 座位数据字典，用于价格排序
    
    Returns:
        排序键元组 (换乘次数, 主排序字段, 总耗时, 出发时间, 到达时间)
    """
    transfers = len(route) - 1
    duration = route_duration(route)
    departure = route[0].depart_abs_min
    arrival = route[-1].arrive_abs_min

    if sort_by == "price" and seat_data:
        price = route_min_price(route, seat_data)
        primary = price if price is not None else float("inf")
    elif sort_by == "departure":
        primary = float(departure)
    else:  # duration（默认）
        primary = float(duration)

    return (transfers, primary, duration, departure, arrival)


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



def exclude_direct_train_codes_in_transfer_routes(
    routes: list[list[Segment]],
    enabled: bool,
) -> list[list[Segment]]:
    """排除在换乘方案中使用直达车次代码的路线。
    
    逻辑：
    1. 收集所有直达方案的 train_code
    2. 过滤掉包含这些 train_code 的换乘方案
    3. 保留所有直达方案
    
    Args:
        routes: 路线列表
        enabled: 是否启用此过滤
    
    Returns:
        过滤后的路线列表
    """
    if not enabled:
        return routes
    
    # 收集所有直达方案的 train_code（大写）
    direct_train_codes = {
        route[0].train_code.upper()
        for route in routes
        if len(route) == 1
    }
    
    if not direct_train_codes:
        return routes
    
    # 过滤：保留直达方案，或不包含直达 train_code 的换乘方案
    return [
        route
        for route in routes
        if len(route) == 1  # 保留所有直达方案
        or all(  # 或换乘方案中不包含任何直达 train_code
            segment.train_code.upper() not in direct_train_codes
            for segment in route
        )
    ]


def filter_routes_by_display_train_types(
    routes: list[list[Segment]],
    display_train_type_prefixes: set[str],
) -> list[list[Segment]]:
    """仅保留所有 Segment 都属于指定车型的路线。
    
    Args:
        routes: 路线列表
        display_train_type_prefixes: 允许显示的车型前缀集合（空表示不过滤）
    
    Returns:
        过滤后的路线列表
    """
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
