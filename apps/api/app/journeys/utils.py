from __future__ import annotations

import hashlib
import json
from datetime import time

from app.journeys.schemas import (
    JourneyResult,
    JourneySegment,
    SeatSchema,
)
from app.models import SeatInfo, SeatLookupKey, Segment
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


def _build_journey_result(
    route: list[Segment],
    seat_data: dict[SeatLookupKey, list[SeatInfo]],
) -> JourneyResult:
    segments: list[JourneySegment] = []
    for seg in route:
        key: SeatLookupKey = (seg.train_no, seg.from_station, seg.to_station)
        seats = [
            SeatSchema(
                seat_type=s.seat_type,
                status=s.status,
                price=s.price,
                available=s.available,
            )
            for s in seat_data.get(key, [])
        ]
        segments.append(
            JourneySegment(
                train_code=seg.train_code,
                from_station=seg.from_station,
                to_station=seg.to_station,
                departure_time=abs_min_to_hhmm(seg.depart_abs_min),
                arrival_time=abs_min_to_hhmm(seg.arrive_abs_min),
                duration_minutes=seg.arrive_abs_min - seg.depart_abs_min,
                seats=seats,
            )
        )

    available_prices = [
        s.price
        for seg in route
        for s in seat_data.get((seg.train_no, seg.from_station, seg.to_station), [])
        if s.price is not None and s.available
    ]
    min_price = min(available_prices) if available_prices else None
    total_duration = route[-1].arrive_abs_min - route[0].depart_abs_min

    return JourneyResult(
        id=_route_id(route),
        is_direct=len(route) == 1,
        total_duration_minutes=total_duration,
        departure_time=abs_min_to_hhmm(route[0].depart_abs_min),
        arrival_time=abs_min_to_hhmm(route[-1].arrive_abs_min),
        min_price=min_price,
        segments=segments,
    )
