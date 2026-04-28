from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.models import Segment, Timetable
from app.planner.filters import (
    is_departure_time_allowed,
    is_train_token_excluded,
    is_train_type_allowed,
    is_train_type_excluded,
    route_matches_allowed_trains,
    route_matches_allowed_transfer_stations,
)
from app.planner.index import SearchIndex


@dataclass(frozen=True)
class PartialRoute:
    segments: tuple[Segment, ...]

    @property
    def start_station(self) -> str:
        return self.segments[0].from_station

    @property
    def end_station(self) -> str:
        return self.segments[-1].to_station

    @property
    def first_depart(self) -> int:
        return self.segments[0].depart_abs_min

    @property
    def last_arrive(self) -> int:
        return self.segments[-1].arrive_abs_min

    @property
    def first_train_no(self) -> str:
        return self.segments[0].train_no

    @property
    def last_train_no(self) -> str:
        return self.segments[-1].train_no

    def append(self, segment: Segment) -> PartialRoute:
        return PartialRoute((*self.segments, segment))

    def prepend(self, segment: Segment) -> PartialRoute:
        return PartialRoute((segment, *self.segments))


def _route_key(route: Iterable[Segment]) -> tuple[tuple[str, str, str, int, int], ...]:
    return tuple(
        (s.train_no, s.from_station, s.to_station, s.depart_abs_min, s.arrive_abs_min)
        for s in route
    )


def _is_train_allowed(
    train_no: str,
    train_code: str,
    allowed_type_prefixes: tuple[str, ...],
    excluded_type_prefixes: set[str],
    excluded_tokens: set[str],
) -> bool:
    return (
        is_train_type_allowed(train_code, allowed_type_prefixes)
        and not is_train_type_excluded(train_code, excluded_type_prefixes)
        and not is_train_token_excluded(train_no, train_code, excluded_tokens)
    )


def _build_segment(
    train_no: str,
    board_index: int,
    alight_index: int,
    timetable: Timetable,
) -> Segment | None:
    events = timetable[train_no]
    board_event = events[board_index]
    alight_event = events[alight_index]
    depart_abs = board_event.depart_abs_min
    arrive_abs = alight_event.arrive_abs_min

    if depart_abs is None or arrive_abs is None or arrive_abs <= depart_abs:
        return None

    return Segment(
        train_no=train_no,
        train_code=board_event.train_code or alight_event.train_code,
        from_station=board_event.station_name,
        to_station=alight_event.station_name,
        depart_abs_min=depart_abs,
        arrive_abs_min=arrive_abs,
        total_stops=board_event.total_stops,
    )


def _iter_forward_segments(
    station: str,
    earliest_depart: int,
    latest_depart: int | None,
    exclude_train_no: str | None,
    allowed_end_stations: set[str] | None,
    arrival_deadline_abs_min: int | None,
    allowed_type_prefixes: tuple[str, ...],
    excluded_type_prefixes: set[str],
    excluded_tokens: set[str],
    timetable: Timetable,
    index: SearchIndex,
) -> Iterable[Segment]:
    for train_no, board_index in index.departures_by_station.get(station, []):
        if exclude_train_no and train_no == exclude_train_no:
            continue

        board_event = timetable[train_no][board_index]
        depart_abs = board_event.depart_abs_min
        if depart_abs is None:
            continue
        if depart_abs < earliest_depart:
            continue
        if latest_depart is not None and depart_abs > latest_depart:
            break
        if not _is_train_allowed(
            train_no,
            board_event.train_code,
            allowed_type_prefixes,
            excluded_type_prefixes,
            excluded_tokens,
        ):
            continue

        for alight_index in range(board_index + 1, len(timetable[train_no])):
            alight_event = timetable[train_no][alight_index]
            arrive_abs = alight_event.arrive_abs_min
            if arrive_abs is None or arrive_abs <= depart_abs:
                continue
            if arrival_deadline_abs_min is not None and arrive_abs > arrival_deadline_abs_min:
                break
            if (
                allowed_end_stations is not None
                and alight_event.station_name not in allowed_end_stations
            ):
                continue

            segment = _build_segment(train_no, board_index, alight_index, timetable)
            if segment is not None:
                yield segment


def _iter_backward_segments(
    station: str,
    earliest_arrive: int | None,
    latest_arrive: int | None,
    exclude_train_no: str | None,
    allowed_start_stations: set[str] | None,
    allowed_type_prefixes: tuple[str, ...],
    excluded_type_prefixes: set[str],
    excluded_tokens: set[str],
    timetable: Timetable,
    index: SearchIndex,
) -> Iterable[Segment]:
    for train_no, alight_index in index.arrivals_by_station.get(station, []):
        if exclude_train_no and train_no == exclude_train_no:
            continue

        alight_event = timetable[train_no][alight_index]
        arrive_abs = alight_event.arrive_abs_min
        if arrive_abs is None:
            continue
        if earliest_arrive is not None and arrive_abs < earliest_arrive:
            continue
        if latest_arrive is not None and arrive_abs > latest_arrive:
            break
        if not _is_train_allowed(
            train_no,
            alight_event.train_code,
            allowed_type_prefixes,
            excluded_type_prefixes,
            excluded_tokens,
        ):
            continue

        for board_index in range(0, alight_index):
            board_event = timetable[train_no][board_index]
            if (
                allowed_start_stations is not None
                and board_event.station_name not in allowed_start_stations
            ):
                continue

            segment = _build_segment(train_no, board_index, alight_index, timetable)
            if segment is not None:
                yield segment


def _transfer_wait(prev_segment: Segment, next_segment: Segment) -> int:
    return next_segment.depart_abs_min - prev_segment.arrive_abs_min


def _valid_transfer(
    prev_segment: Segment,
    next_segment: Segment,
    min_transfer_minutes: int,
    max_transfer_minutes: int | None,
    excluded_transfer_stations: set[str],
) -> bool:
    if prev_segment.to_station != next_segment.from_station:
        return False
    if prev_segment.train_no == next_segment.train_no:
        return False
    if prev_segment.to_station in excluded_transfer_stations:
        return False

    wait = _transfer_wait(prev_segment, next_segment)
    if wait < min_transfer_minutes:
        return False
    return max_transfer_minutes is None or wait <= max_transfer_minutes


def _route_is_valid(
    route: tuple[Segment, ...],
    from_stations: set[str],
    to_stations: set[str],
    min_transfer_minutes: int,
    max_transfer_minutes: int | None,
    arrival_deadline_abs_min: int | None,
    departure_time_start_min: int | None,
    departure_time_end_min: int | None,
    departure_time_cross_day: bool,
    excluded_transfer_stations: set[str],
    allowed_transfer_stations: set[str],
    allowed_train_tokens: set[str],
) -> bool:
    if not route:
        return False
    if route[0].from_station not in from_stations or route[-1].to_station not in to_stations:
        return False
    if not is_departure_time_allowed(
        route[0].depart_abs_min,
        departure_time_start_min,
        departure_time_end_min,
        departure_time_cross_day,
    ):
        return False
    if arrival_deadline_abs_min is not None and route[-1].arrive_abs_min > arrival_deadline_abs_min:
        return False

    for prev_segment, next_segment in zip(route, route[1:], strict=False):
        if not _valid_transfer(
            prev_segment,
            next_segment,
            min_transfer_minutes,
            max_transfer_minutes,
            excluded_transfer_stations,
        ):
            return False

    return route_matches_allowed_trains(
        list(route),
        allowed_train_tokens,
    ) and route_matches_allowed_transfer_stations(
        list(route),
        allowed_transfer_stations,
    )


def _index_backward_by_start(
    routes: list[PartialRoute],
) -> dict[str, list[PartialRoute]]:
    result: dict[str, list[PartialRoute]] = {}
    for route in routes:
        result.setdefault(route.start_station, []).append(route)
    return result


def search_journeys(
    from_stations: set[str],
    to_stations: set[str],
    transfer_values: list[int] | None = None,
    *,
    transfer_count: int | None = None,
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
    station_index: SearchIndex,
) -> list[list[Segment]]:
    """Search routes with a bidirectional bounded expansion.

    The product supports at most 3 transfers, so every route has at most 4 train
    legs. We expand from the origin up to 2 legs and from the destination back
    up to 2 legs, then join partial routes at the common transfer station.
    """
    if transfer_values is None:
        transfer_values = [] if transfer_count is None else list(range(transfer_count + 1))

    desired_legs = {transfer_count + 1 for transfer_count in transfer_values}
    if not desired_legs:
        return []
    max_legs = max(desired_legs)
    if max_legs > 4:
        raise ValueError("search_journeys supports at most 3 transfers")

    forward: dict[int, list[PartialRoute]] = {1: [], 2: []}
    backward: dict[int, list[PartialRoute]] = {1: [], 2: []}

    for start_station in sorted(from_stations):
        for segment in _iter_forward_segments(
            station=start_station,
            earliest_depart=0,
            latest_depart=None,
            exclude_train_no=None,
            allowed_end_stations=None,
            arrival_deadline_abs_min=arrival_deadline_abs_min,
            allowed_type_prefixes=allowed_train_type_prefixes,
            excluded_type_prefixes=excluded_train_type_prefixes,
            excluded_tokens=excluded_train_tokens,
            timetable=timetable,
            index=station_index,
        ):
            if is_departure_time_allowed(
                segment.depart_abs_min,
                departure_time_start_min,
                departure_time_end_min,
                departure_time_cross_day,
            ):
                forward[1].append(PartialRoute((segment,)))

    for target_station in sorted(to_stations):
        for segment in _iter_backward_segments(
            station=target_station,
            earliest_arrive=None,
            latest_arrive=arrival_deadline_abs_min,
            exclude_train_no=None,
            allowed_start_stations=None,
            allowed_type_prefixes=allowed_train_type_prefixes,
            excluded_type_prefixes=excluded_train_type_prefixes,
            excluded_tokens=excluded_train_tokens,
            timetable=timetable,
            index=station_index,
        ):
            backward[1].append(PartialRoute((segment,)))

    need_backward_two = any(legs - 1 == 2 or legs - 2 == 2 for legs in desired_legs)
    if need_backward_two:
        allowed_b2_starts: set[str] | None = None
        if 4 not in desired_legs:
            allowed_b2_starts = {route.end_station for route in forward[1]}

        for route in backward[1]:
            transfer_station = route.start_station
            if transfer_station in excluded_transfer_stations:
                continue

            latest_arrive = route.first_depart - min_transfer_minutes
            earliest_arrive = (
                route.first_depart - max_transfer_minutes
                if max_transfer_minutes is not None
                else None
            )
            for segment in _iter_backward_segments(
                station=transfer_station,
                earliest_arrive=earliest_arrive,
                latest_arrive=latest_arrive,
                exclude_train_no=route.first_train_no,
                allowed_start_stations=allowed_b2_starts,
                allowed_type_prefixes=allowed_train_type_prefixes,
                excluded_type_prefixes=excluded_train_type_prefixes,
                excluded_tokens=excluded_train_tokens,
                timetable=timetable,
                index=station_index,
            ):
                backward[2].append(route.prepend(segment))

    backward_by_start = {
        1: _index_backward_by_start(backward[1]),
        2: _index_backward_by_start(backward[2]),
    }

    f2_target_stations: set[str] = set()
    for legs in desired_legs:
        if legs == 2:
            f2_target_stations.update(to_stations)
        if legs == 3:
            f2_target_stations.update(backward_by_start[1])
        if legs == 4:
            f2_target_stations.update(backward_by_start[2])

    if max_legs >= 2 and f2_target_stations:
        for route in forward[1]:
            transfer_station = route.end_station
            if transfer_station in excluded_transfer_stations:
                continue

            latest_depart = (
                route.last_arrive + max_transfer_minutes
                if max_transfer_minutes is not None
                else None
            )
            for segment in _iter_forward_segments(
                station=transfer_station,
                earliest_depart=route.last_arrive + min_transfer_minutes,
                latest_depart=latest_depart,
                exclude_train_no=route.last_train_no,
                allowed_end_stations=f2_target_stations,
                arrival_deadline_abs_min=arrival_deadline_abs_min,
                allowed_type_prefixes=allowed_train_type_prefixes,
                excluded_type_prefixes=excluded_train_type_prefixes,
                excluded_tokens=excluded_train_tokens,
                timetable=timetable,
                index=station_index,
            ):
                forward[2].append(route.append(segment))

    results: list[list[Segment]] = []
    seen: set[tuple[tuple[str, str, str, int, int], ...]] = set()

    def add_route(route: tuple[Segment, ...]) -> None:
        if len(route) not in desired_legs:
            return
        if not _route_is_valid(
            route,
            from_stations,
            to_stations,
            min_transfer_minutes,
            max_transfer_minutes,
            arrival_deadline_abs_min,
            departure_time_start_min,
            departure_time_end_min,
            departure_time_cross_day,
            excluded_transfer_stations,
            allowed_transfer_stations,
            allowed_train_tokens,
        ):
            return

        key = _route_key(route)
        if key in seen:
            return
        seen.add(key)
        results.append(list(route))

    for length, routes in forward.items():
        if length in desired_legs:
            for route in routes:
                if route.end_station in to_stations:
                    add_route(route.segments)

    for forward_length, forward_routes in forward.items():
        if not forward_routes:
            continue
        for legs in desired_legs:
            backward_length = legs - forward_length
            if backward_length not in (1, 2):
                continue

            candidates_by_start = backward_by_start[backward_length]
            for forward_route in forward_routes:
                for backward_route in candidates_by_start.get(forward_route.end_station, []):
                    route = (*forward_route.segments, *backward_route.segments)
                    add_route(route)

    return results
