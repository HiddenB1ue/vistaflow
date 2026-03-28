from __future__ import annotations

from app.domain.models import Segment, SeatInfo
from app.domain.types import SeatLookupKey, StationIndex, Timetable
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
    transfer_count: int,
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

    每个方案是一个 Segment 列表，列表长度 = transfer_count + 1。
    包含换乘次数更少的方案（transfer_count=0 时仅返回直达）。
    """
    results: list[list[Segment]] = []
    seen: set[tuple[tuple[str, str, str, int, int], ...]] = set()
    required_legs = transfer_count + 1

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
                if is_last_leg:
                    if alight_event.station_name in to_stations:
                        if route_matches_allowed_trains(
                            path, allowed_train_tokens
                        ) and route_matches_allowed_transfer_stations(
                            path, allowed_transfer_stations
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

    # 支持更少换乘的方案（如请求2次换乘，也返回直达和1次换乘）
    min_legs = 1
    for legs in range(min_legs, required_legs + 1):
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
