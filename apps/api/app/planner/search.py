from __future__ import annotations

import bisect
import heapq
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

MINUTES_PER_DAY = 1440


@dataclass(frozen=True)
class SearchLabel:
    station: str
    time_abs_min: int
    route: tuple[Segment, ...]


def _route_key(route: Iterable[Segment]) -> tuple[tuple[str, str, str, int, int], ...]:
    return tuple(
        (
            s.service_id or s.train_no,
            s.from_station,
            s.to_station,
            s.depart_abs_min,
            s.arrive_abs_min,
        )
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


def _public_train_no(service_id: str, event_train_no: str) -> str:
    if event_train_no and event_train_no == service_id and ":" in event_train_no:
        return event_train_no.split(":", 1)[1]
    if event_train_no:
        return event_train_no
    if ":" in service_id:
        return service_id.split(":", 1)[1]
    return service_id


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
        train_no=_public_train_no(train_no, board_event.train_no),
        train_code=board_event.train_code or alight_event.train_code,
        from_station=board_event.station_name,
        to_station=alight_event.station_name,
        depart_abs_min=depart_abs,
        arrive_abs_min=arrive_abs,
        total_stops=board_event.total_stops,
        service_id=board_event.service_id or train_no,
        run_date=board_event.run_date,
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
    entries = index.departures_by_station.get(station, [])
    if not entries:
        return

    depart_times = [
        timetable[train_no][board_index].depart_abs_min or 0
        for train_no, board_index in entries
    ]
    start = bisect.bisect_left(depart_times, earliest_depart)
    stop = (
        len(entries)
        if latest_depart is None
        else bisect.bisect_right(depart_times, latest_depart)
    )

    for train_no, board_index in entries[start:stop]:
        if exclude_train_no and train_no == exclude_train_no:
            continue

        board_event = timetable[train_no][board_index]
        depart_abs = board_event.depart_abs_min
        if depart_abs is None:
            continue
        if not _is_train_allowed(
            _public_train_no(train_no, board_event.train_no),
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
    if (prev_segment.service_id or prev_segment.train_no) == (
        next_segment.service_id or next_segment.train_no
    ):
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
    if (
        arrival_deadline_abs_min is not None
        and route[-1].arrive_abs_min % MINUTES_PER_DAY > arrival_deadline_abs_min
    ):
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


def _is_arrival_allowed(
    arrive_abs_min: int,
    latest_arrival_abs_min: int | None,
    arrival_deadline_abs_min: int | None,
) -> bool:
    if latest_arrival_abs_min is not None and arrive_abs_min > latest_arrival_abs_min:
        return False
    if arrival_deadline_abs_min is None:
        return True
    return arrive_abs_min % MINUTES_PER_DAY <= arrival_deadline_abs_min


def _append_pruned_label(
    labels: dict[tuple[str, int], list[SearchLabel]],
    label: SearchLabel,
    max_labels_per_state: int = 4,
) -> bool:
    key = (label.station, len(label.route))
    bucket = labels.setdefault(key, [])
    for existing in bucket:
        if existing.time_abs_min <= label.time_abs_min:
            existing_trains = tuple(seg.service_id or seg.train_no for seg in existing.route)
            next_trains = tuple(seg.service_id or seg.train_no for seg in label.route)
            if existing_trains == next_trains:
                return False
    bucket.append(label)
    bucket.sort(key=lambda item: item.time_abs_min)
    if len(bucket) > max_labels_per_state:
        bucket[:] = bucket[:max_labels_per_state]
        return label in bucket
    return True


def _build_reachable_to_targets(
    timetable: Timetable,
    to_stations: set[str],
    max_legs: int,
) -> dict[int, set[str]]:
    reachable: dict[int, set[str]] = {0: set(to_stations)}
    for legs in range(1, max_legs + 1):
        next_stations = set(reachable[legs - 1])
        targets = reachable[legs - 1]
        for events in timetable.values():
            can_reach_target = False
            for event in reversed(events):
                if event.station_name in targets:
                    can_reach_target = True
                if can_reach_target:
                    next_stations.add(event.station_name)
        reachable[legs] = next_stations
    return reachable


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
    search_start_abs_min: int = 0,
    first_departure_latest_abs_min: int = MINUTES_PER_DAY - 1,
    latest_arrival_abs_min: int | None = (3 * MINUTES_PER_DAY) - 1,
    timetable: Timetable,
    station_index: SearchIndex,
) -> list[list[Segment]]:
    """Search routes with a bounded forward label expansion over absolute time."""
    if transfer_values is None:
        transfer_values = [] if transfer_count is None else list(range(transfer_count + 1))

    desired_legs = {transfer_count + 1 for transfer_count in transfer_values}
    if not desired_legs:
        return []
    max_legs = max(desired_legs)
    if max_legs > 4:
        raise ValueError("search_journeys supports at most 3 transfers")

    results: list[list[Segment]] = []
    seen: set[tuple[tuple[str, str, str, int, int], ...]] = set()
    reachable_to_target = _build_reachable_to_targets(timetable, to_stations, max_legs)

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

    queue: list[tuple[int, int, SearchLabel]] = []
    labels_by_state: dict[tuple[str, int], list[SearchLabel]] = {}
    sequence = 0
    for station in sorted(from_stations):
        label = SearchLabel(station=station, time_abs_min=search_start_abs_min, route=())
        heapq.heappush(queue, (label.time_abs_min, sequence, label))
        sequence += 1

    while queue:
        _, _, label = heapq.heappop(queue)
        if len(label.route) >= max_legs:
            continue

        is_first_leg = len(label.route) == 0
        remaining_after_this_leg = max_legs - len(label.route) - 1
        allowed_end_stations = reachable_to_target.get(remaining_after_this_leg, to_stations)
        earliest_depart = (
            search_start_abs_min if is_first_leg else label.time_abs_min + min_transfer_minutes
        )
        latest_depart = first_departure_latest_abs_min if is_first_leg else None
        if not is_first_leg and max_transfer_minutes is not None:
            latest_depart = label.time_abs_min + max_transfer_minutes

        exclude_service_id = label.route[-1].service_id if label.route else None
        for segment in _iter_forward_segments(
            station=label.station,
            earliest_depart=earliest_depart,
            latest_depart=latest_depart,
            exclude_train_no=exclude_service_id,
            allowed_end_stations=allowed_end_stations,
            arrival_deadline_abs_min=latest_arrival_abs_min,
            allowed_type_prefixes=allowed_train_type_prefixes,
            excluded_type_prefixes=excluded_train_type_prefixes,
            excluded_tokens=excluded_train_tokens,
            timetable=timetable,
            index=station_index,
        ):
            if is_first_leg and not is_departure_time_allowed(
                segment.depart_abs_min,
                departure_time_start_min,
                departure_time_end_min,
                departure_time_cross_day,
            ):
                continue
            if not is_first_leg and not _valid_transfer(
                label.route[-1],
                segment,
                min_transfer_minutes,
                max_transfer_minutes,
                excluded_transfer_stations,
            ):
                continue
            if not _is_arrival_allowed(
                segment.arrive_abs_min,
                latest_arrival_abs_min,
                arrival_deadline_abs_min if segment.to_station in to_stations else None,
            ):
                continue

            next_route = (*label.route, segment)
            if segment.to_station in to_stations:
                add_route(next_route)
                continue

            if len(next_route) < max_legs and segment.to_station not in excluded_transfer_stations:
                next_label = SearchLabel(
                    station=segment.to_station,
                    time_abs_min=segment.arrive_abs_min,
                    route=next_route,
                )
                if _append_pruned_label(labels_by_state, next_label):
                    heapq.heappush(queue, (next_label.time_abs_min, sequence, next_label))
                    sequence += 1

    return results
