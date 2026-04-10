from __future__ import annotations

from app.models import Segment, StationIndex, Timetable
from app.planner.filters import (
    get_boardable_trains,
    is_departure_time_allowed,
    route_matches_allowed_trains,
    route_matches_allowed_transfer_stations,
)


def _route_key(route: list[Segment]) -> tuple[tuple[str, str, str, int, int], ...]:
    return tuple(
        (s.train_no, s.from_station, s.to_station, s.depart_abs_min, s.arrive_abs_min)
        for s in route
    )


def search_journeys(
    from_stations: set[str],
    to_stations: set[str],
    transfer_values: list[int],
    min_transfer_minutes: int,
    max_transfer_minutes: int | None,
    arrival_deadline_abs_min: int | None,
    departure_time_start_min: int | None,
    departure_time_end_min: int | None,
    departure_time_cross_day: bool,
    excluded_transfer_stations: set[str],
    allowed_transfer_stations: set[str],
    allowed_train_type_prefixes: tuple[str, ...],
    excluded_train_type_prefixes: set[str],
    excluded_train_tokens: set[str],
    allowed_train_tokens: set[str],
    timetable: Timetable,
    station_index: StationIndex,
) -> list[list[Segment]]:
    """DFS 搜索满足条件的行程方案列表。

    支持多换乘次数搜索（如 transfer_values=[0, 1, 2] 表示搜索直达、1次换乘、2次换乘）。
    使用 seen 集合去重，避免重复路线。
    
    Args:
        from_stations: 出发站集合
        to_stations: 到达站集合
        transfer_values: 换乘次数列表（如 [0, 1, 2] 或 [2]）
        min_transfer_minutes: 最小换乘时间（分钟）
        max_transfer_minutes: 最大换乘时间（分钟），None 表示无限制
        arrival_deadline_abs_min: 到达截止时间（绝对分钟数），None 表示无限制
        departure_time_start_min: 出发时间窗口开始（分钟数），None 表示无限制
        departure_time_end_min: 出发时间窗口结束（分钟数），None 表示无限制
        departure_time_cross_day: 出发时间窗口是否跨天
        excluded_transfer_stations: 排除的换乘站集合
        allowed_transfer_stations: 允许的换乘站集合（空表示不限制）
        allowed_train_type_prefixes: 允许的车型前缀元组（空表示不限制）
        excluded_train_type_prefixes: 排除的车型前缀集合
        excluded_train_tokens: 排除的车次标识符集合
        allowed_train_tokens: 允许的车次标识符集合（空表示不限制）
        timetable: 时刻表
        station_index: 站点索引
    
    Returns:
        满足条件的路线列表，每个路线是 Segment 列表
    """
    results: list[list[Segment]] = []
    seen: set[tuple[tuple[str, str, str, int, int], ...]] = set()

    def dfs(
        current_station: str,
        earliest_depart: int,
        latest_depart: int | None,
        legs_remaining: int,
        is_first_leg: bool,
        path: list[Segment],
        last_train_no: str | None,
    ) -> None:
        if legs_remaining == 0:
            return

        candidates = get_boardable_trains(
            station=current_station,
            earliest_depart=earliest_depart,
            latest_depart=latest_depart,
            exclude_train_no=last_train_no,
            allowed_type_prefixes=allowed_train_type_prefixes,
            excluded_type_prefixes=excluded_train_type_prefixes,
            excluded_tokens=excluded_train_tokens,
            timetable=timetable,
            station_index=station_index,
        )

        for train_no, board_idx, depart_abs in candidates:
            board_event = timetable[train_no][board_idx]

            if is_first_leg and not is_departure_time_allowed(
                depart_abs,
                departure_time_start_min,
                departure_time_end_min,
                departure_time_cross_day,
            ):
                continue

            events = timetable[train_no]
            for alight_event in events[board_idx + 1 :]:
                arrive_abs = alight_event.arrive_abs_min
                if arrive_abs is None or arrive_abs <= depart_abs:
                    continue
                if (
                    arrival_deadline_abs_min is not None
                    and arrive_abs > arrival_deadline_abs_min
                ):
                    break

                segment = Segment(
                    train_no=train_no,
                    train_code=board_event.train_code or alight_event.train_code,
                    from_station=board_event.station_name,
                    to_station=alight_event.station_name,
                    depart_abs_min=depart_abs,
                    arrive_abs_min=arrive_abs,
                )
                path.append(segment)

                is_last_leg = legs_remaining == 1
                if (
                    is_last_leg
                    and alight_event.station_name in to_stations
                    and route_matches_allowed_trains(path, allowed_train_tokens)
                    and route_matches_allowed_transfer_stations(
                        path, allowed_transfer_stations
                    )
                ):
                    key = _route_key(path)
                    if key not in seen:
                        seen.add(key)
                        results.append(list(path))
                else:
                    if alight_event.station_name not in excluded_transfer_stations:
                        next_earliest = arrive_abs + min_transfer_minutes
                        next_latest = (
                            arrive_abs + max_transfer_minutes
                            if max_transfer_minutes is not None
                            else None
                        )
                        dfs(
                            current_station=alight_event.station_name,
                            earliest_depart=next_earliest,
                            latest_depart=next_latest,
                            legs_remaining=legs_remaining - 1,
                            is_first_leg=False,
                            path=path,
                            last_train_no=train_no,
                        )

                path.pop()

    # 支持多换乘次数搜索（单次 DFS 遍历）
    for transfer_count in transfer_values:
        legs = transfer_count + 1
        for start_station in sorted(from_stations):
            dfs(
                current_station=start_station,
                earliest_depart=0,
                latest_depart=None,
                legs_remaining=legs,
                is_first_leg=True,
                path=[],
                last_train_no=None,
            )

    return results
