from __future__ import annotations

import hashlib
import json
from datetime import time

from app.domain.models import SeatInfo, Segment
from app.domain.types import SeatLookupKey
from app.integrations.ticket_12306.client import AbstractTicketClient
from app.planner.index import build_station_index
from app.planner.ranking import apply_display_limit, group_and_rank
from app.planner.search import search_journeys
from app.planner.time_utils import abs_min_to_hhmm
from app.repositories.station_repository import StationRepository
from app.repositories.timetable_repository import TimetableRepository
from app.schemas.journey import (
    JourneyResult,
    JourneySearchRequest,
    JourneySearchResponse,
    JourneySegment,
    SeatSchema,
)
from app.services.exceptions import BusinessError


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


class JourneyService:
    def __init__(
        self,
        timetable_repo: TimetableRepository,
        station_repo: StationRepository,
        ticket_client: AbstractTicketClient,
    ) -> None:
        self._timetable_repo = timetable_repo
        self._station_repo = station_repo
        self._ticket_client = ticket_client

    async def search(self, req: JourneySearchRequest) -> JourneySearchResponse:
        run_date = req.date.isoformat()

        timetable = await self._timetable_repo.load_timetable(
            run_date=run_date,
            filter_running_only=req.filter_running_only,
        )
        if not timetable:
            raise BusinessError("暂无该日期的列车时刻数据", http_status=404)

        station_index = build_station_index(timetable)

        routes = search_journeys(
            from_stations={req.from_station.strip()},
            to_stations={req.to_station.strip()},
            transfer_count=req.transfer_count,
            min_transfer_minutes=req.min_transfer_minutes,
            max_transfer_minutes=req.max_transfer_minutes,
            arrival_deadline_abs_min=_time_to_abs_min(req.arrival_deadline),
            departure_time_start_min=_time_to_abs_min(req.departure_time_start),
            departure_time_end_min=_time_to_abs_min(req.departure_time_end),
            departure_time_cross_day=_is_cross_day(
                req.departure_time_start, req.departure_time_end
            ),
            excluded_transfer_stations=set(),
            allowed_transfer_stations=set(),
            allowed_train_type_prefixes=tuple(t.upper() for t in req.allowed_train_types),
            excluded_train_type_prefixes={t.upper() for t in req.excluded_train_types},
            excluded_train_tokens=set(),
            allowed_train_tokens=set(),
            timetable=timetable,
            station_index=station_index,
        )

        seat_data: dict[SeatLookupKey, list[SeatInfo]] = {}

        if req.enable_ticket_enrich and routes:
            segment_keys: set[SeatLookupKey] = {
                (seg.train_no, seg.from_station, seg.to_station)
                for route in routes
                for seg in route
            }
            station_names = {
                name
                for train_no, from_s, to_s in segment_keys
                for name in (from_s, to_s)
            }
            telecodes = await self._station_repo.get_telecodes_by_names(station_names)
            train_codes: dict[SeatLookupKey, str] = {
                (seg.train_no, seg.from_station, seg.to_station): seg.train_code
                for route in routes
                for seg in route
            }
            live_data = await self._ticket_client.fetch_tickets(
                run_date=run_date,
                segments=segment_keys,
                telecodes=telecodes,
                train_codes=train_codes,
            )
            seat_data = {key: ticket_seg.seats for key, ticket_seg in live_data.items()}

        ranked = group_and_rank(
            routes,
            sort_by="duration",
            top_n_per_sequence=1,
            seat_data=seat_data if seat_data else None,
        )
        ranked = apply_display_limit(ranked, req.display_limit)

        journeys = [_build_journey_result(route, seat_data) for route in ranked]
        return JourneySearchResponse(
            journeys=journeys,
            total=len(journeys),
            date=run_date,
        )
