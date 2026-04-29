from __future__ import annotations

import hashlib
import json
from datetime import date, time, timedelta

from app.journeys.schemas import (
    JourneyResult,
    JourneySegment,
)
from app.models import Segment
from app.planner.time_utils import abs_min_to_hhmm


def _time_to_abs_min(t: time | None) -> int | None:
    if t is None:
        return None
    return t.hour * 60 + t.minute


def _is_cross_day(start: time | None, end: time | None) -> bool:
    if start is None or end is None:
        return False
    return end < start


def _route_id(route: list[Segment]) -> str:
    key = json.dumps(
        [(s.train_no, s.from_station, s.to_station, s.depart_abs_min) for s in route]
    )
    return hashlib.md5(key.encode()).hexdigest()[:12]  # noqa: S324


def _date_for_abs_min(search_date: str, abs_min: int) -> str:
    base_date = date.fromisoformat(search_date)
    return (base_date + timedelta(days=abs_min // 1440)).isoformat()


def _build_journey_result(route: list[Segment], search_date: str) -> JourneyResult:
    segments = [
        JourneySegment(
            train_no=seg.train_no,
            train_code=seg.train_code,
            from_station=seg.from_station,
            to_station=seg.to_station,
            departure_date=_date_for_abs_min(search_date, seg.depart_abs_min),
            departure_time=abs_min_to_hhmm(seg.depart_abs_min),
            arrival_date=_date_for_abs_min(search_date, seg.arrive_abs_min),
            arrival_time=abs_min_to_hhmm(seg.arrive_abs_min),
            duration_minutes=seg.arrive_abs_min - seg.depart_abs_min,
            stops_count=seg.total_stops or 0,
        )
        for seg in route
    ]

    total_duration = route[-1].arrive_abs_min - route[0].depart_abs_min

    return JourneyResult(
        id=_route_id(route),
        is_direct=len(route) == 1,
        total_duration_minutes=total_duration,
        departure_date=_date_for_abs_min(search_date, route[0].depart_abs_min),
        departure_time=abs_min_to_hhmm(route[0].depart_abs_min),
        arrival_date=_date_for_abs_min(search_date, route[-1].arrive_abs_min),
        arrival_time=abs_min_to_hhmm(route[-1].arrive_abs_min),
        segments=segments,
    )
