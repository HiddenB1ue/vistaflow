from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

from redis.asyncio import Redis

from app.exceptions import NotFoundError
from app.integrations.ticket_12306.service import SEAT_LABELS, Ticket12306Service
from app.journey_search_sessions.schemas import (
    CachedRouteCandidate,
    CachedTrainSegment,
    PriceCacheEntry,
    RoutePointResponse,
    RouteResponse,
    RouteSeatResponse,
    RouteStationResponse,
    RouteTrainSegmentResponse,
    RouteTransferSegmentResponse,
    SearchSessionAvailableFacetsResponse,
    SearchSessionCacheRecord,
    SearchSessionCreateRequest,
    SearchSessionCreateResponse,
    SearchSessionDeleteResponse,
    SearchSessionSummaryResponse,
    SearchSessionViewRequest,
    SearchSessionViewResponse,
    SearchSessionViewResultResponse,
    SearchSummaryResponse,
    price_map_key,
)
from app.journeys.schemas import JourneyResult, JourneySearchResponse
from app.journeys.service import JourneyService
from app.railway.repository import StationRepository


def _get_train_type(train_code: str) -> str:
    code = train_code.strip().upper()
    return code[:1] if code else ""


class JourneySearchSessionService:
    def __init__(
        self,
        redis_client: Redis,
        ttl_seconds: int,
        journey_service: JourneyService,
        station_repo: StationRepository,
        ticket_service: Ticket12306Service,
        max_prefetch_concurrency: int = 5,
    ) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds
        self._journey_service = journey_service
        self._station_repo = station_repo
        self._ticket_service = ticket_service
        self._max_prefetch_concurrency = max_prefetch_concurrency

    async def create_session(
        self,
        payload: SearchSessionCreateRequest,
    ) -> SearchSessionCreateResponse:
        search_request = payload.to_journey_request().model_copy(
            update={
                "sort_by": "duration",
                "train_sequence_top_n": 0,
                "display_limit": 100000,
                "display_train_types": [],
                "exclude_direct_train_codes_in_transfer_routes": False,
            }
        )
        search_response = await self._journey_service.search(search_request)
        candidates = await self._build_candidates(search_response)

        price_map = await self._ticket_service.prefetch_all_prices(
            run_date=payload.date.isoformat(),
            candidates=candidates,
            max_concurrency=self._max_prefetch_concurrency,
        )

        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=self._ttl_seconds)
        search_id = uuid4().hex
        summary = SearchSummaryResponse(
            fromStation=payload.from_station.strip(),
            toStation=payload.to_station.strip(),
            date=payload.date.isoformat(),
            totalCandidates=len(candidates),
        )
        record = SearchSessionCacheRecord(
            searchId=search_id,
            createdAt=now,
            expiresAt=expires_at,
            searchQuery=payload,
            searchSummary=summary,
            candidates=candidates,
            price_map=price_map,
        )
        await self._redis.setex(
            self._redis_key(search_id),
            self._ttl_seconds,
            record.model_dump_json(),
        )

        view_request = payload.view or SearchSessionViewRequest()
        view_result = await self._build_view_result(candidates, payload.date.isoformat(), view_request, price_map)
        return SearchSessionCreateResponse(
            searchId=search_id,
            expiresAt=expires_at,
            searchSummary=summary,
            viewResult=view_result,
        )

    async def get_summary(self, search_id: str) -> SearchSessionSummaryResponse:
        record = await self._load_record(search_id)
        return SearchSessionSummaryResponse(
            searchId=record.searchId,
            expiresAt=record.expiresAt,
            searchSummary=record.searchSummary,
        )

    async def get_view(
        self,
        search_id: str,
        payload: SearchSessionViewRequest,
    ) -> SearchSessionViewResultResponse:
        record = await self._load_record(search_id)
        return await self._build_view_result(
            record.candidates,
            record.searchSummary.date,
            payload,
            record.price_map,
        )

    async def delete_session(self, search_id: str) -> SearchSessionDeleteResponse:
        deleted = await self._redis.delete(self._redis_key(search_id))
        return SearchSessionDeleteResponse(deleted=bool(deleted))

    async def _load_record(self, search_id: str) -> SearchSessionCacheRecord:
        raw = await self._redis.get(self._redis_key(search_id))
        if raw is None:
            raise NotFoundError("搜索会话不存在或已过期")
        return SearchSessionCacheRecord.model_validate(json.loads(raw))

    async def _build_candidates(
        self,
        search_response: JourneySearchResponse,
    ) -> list[CachedRouteCandidate]:
        station_names = {
            station_name
            for journey in search_response.journeys
            for segment in journey.segments
            for station_name in (segment.from_station, segment.to_station)
        }
        geo_map = await self._station_repo.get_geo_by_names(list(station_names))
        return [self._build_candidate(journey, geo_map) for journey in search_response.journeys]

    def _build_candidate(
        self,
        journey: JourneyResult,
        geo_map: dict[str, tuple[float, float]],
    ) -> CachedRouteCandidate:
        train_segments: list[CachedTrainSegment | RouteTransferSegmentResponse] = []
        train_types: list[str] = []
        train_codes: list[str] = []
        path_points: list[RoutePointResponse] = []
        seen_path_points: set[str] = set()

        for index, segment in enumerate(journey.segments):
            train_types.append(_get_train_type(segment.train_code))
            train_codes.append(segment.train_code.strip().upper())

            train_segments.append(
                CachedTrainSegment(
                    trainNo=segment.train_no,
                    no=segment.train_code,
                    origin=self._build_station(segment.from_station, geo_map),
                    destination=self._build_station(segment.to_station, geo_map),
                    departureDate=segment.departure_date,
                    departureTime=segment.departure_time,
                    arrivalDate=segment.arrival_date,
                    arrivalTime=segment.arrival_time,
                    stopsCount=segment.stops_count,
                )
            )

            for station_name in (segment.from_station, segment.to_station):
                if station_name in seen_path_points:
                    continue
                seen_path_points.add(station_name)
                lng, lat = geo_map.get(station_name, (0.0, 0.0))
                path_points.append(RoutePointResponse(lng=lng, lat=lat))

            if index < len(journey.segments) - 1:
                next_segment = journey.segments[index + 1]
                train_segments.append(
                    RouteTransferSegmentResponse(
                        transfer=f"{segment.to_station} 换乘 {next_segment.train_code}"
                    )
                )

        first_segment = journey.segments[0]
        last_segment = journey.segments[-1]
        return CachedRouteCandidate(
            id=journey.id,
            trainNo=" / ".join(segment.train_code for segment in journey.segments),
            type="直达" if journey.is_direct else f"中转 {len(journey.segments) - 1} 次",
            origin=self._build_station(first_segment.from_station, geo_map),
            destination=self._build_station(last_segment.to_station, geo_map),
            departureDate=journey.departure_date,
            departureTime=journey.departure_time,
            arrivalDate=journey.arrival_date,
            arrivalTime=journey.arrival_time,
            durationMinutes=journey.total_duration_minutes,
            segs=train_segments,
            pathPoints=path_points,
            isDirect=journey.is_direct,
            transferCount=max(len(journey.segments) - 1, 0),
            trainTypes=sorted({item for item in train_types if item}),
            trainCodes=train_codes,
        )

    def _build_station(
        self,
        name: str,
        geo_map: dict[str, tuple[float, float]],
    ) -> RouteStationResponse:
        lng, lat = geo_map.get(name, (0.0, 0.0))
        return RouteStationResponse(name=name, lng=lng, lat=lat)

    async def _build_view_result(
        self,
        candidates: list[CachedRouteCandidate],
        run_date: str,
        payload: SearchSessionViewRequest,
        price_map: dict[str, PriceCacheEntry] | None = None,
    ) -> SearchSessionViewResultResponse:
        if price_map is None:
            price_map = {}

        filtered = list(candidates)
        facets = self._build_available_facets(candidates)
        applied_view = self._build_applied_view(payload)

        allowed_transfer_counts = set(applied_view.transferCounts)
        if allowed_transfer_counts:
            filtered = [
                candidate
                for candidate in filtered
                if candidate.transferCount in allowed_transfer_counts
            ]

        if payload.exclude_direct_train_codes_in_transfer_routes:
            direct_codes = {
                code
                for candidate in candidates
                if candidate.isDirect
                for code in candidate.trainCodes
            }
            filtered = [
                candidate
                for candidate in filtered
                if candidate.isDirect
                or all(code not in direct_codes for code in candidate.trainCodes)
            ]

        allowed_train_types = set(applied_view.displayTrainTypes)
        if allowed_train_types:
            filtered = [
                candidate
                for candidate in filtered
                if all(train_type in allowed_train_types for train_type in candidate.trainTypes)
            ]

        filtered.sort(key=lambda candidate: self._sort_key(candidate, payload.sort_by, price_map))
        total = len(filtered)
        start = (payload.page - 1) * payload.page_size
        end = start + payload.page_size
        items = [self._to_route_response(candidate) for candidate in filtered[start:end]]

        if not payload.include_tickets:
            items = [self._mark_route_disabled(route) for route in items]
        elif price_map:
            items = [self._apply_prices_from_map(route, price_map) for route in items]
        else:
            items = await self._ticket_service.enrich_routes_for_view(
                run_date=run_date,
                routes=items,
            )

        return SearchSessionViewResultResponse.build(
            items=items,
            total=total,
            view=applied_view,
            facets=facets,
        )

    def _to_route_response(self, candidate: CachedRouteCandidate) -> RouteResponse:
        return RouteResponse(
            id=candidate.id,
            trainNo=candidate.trainNo,
            type=candidate.type,
            origin=candidate.origin,
            destination=candidate.destination,
            departureDate=candidate.departureDate,
            departureTime=candidate.departureTime,
            arrivalDate=candidate.arrivalDate,
            arrivalTime=candidate.arrivalTime,
            durationMinutes=candidate.durationMinutes,
            segs=[
                RouteTrainSegmentResponse.model_validate(segment.model_dump())
                if isinstance(segment, CachedTrainSegment)
                else segment
                for segment in candidate.segs
            ],
            pathPoints=candidate.pathPoints,
        )

    def _build_available_facets(
        self,
        candidates: list[CachedRouteCandidate],
    ) -> SearchSessionAvailableFacetsResponse:
        return SearchSessionAvailableFacetsResponse(
            transferCounts=sorted({candidate.transferCount for candidate in candidates}),
            trainTypes=sorted(
                {train_type for candidate in candidates for train_type in candidate.trainTypes}
            ),
        )

    def _build_applied_view(
        self,
        payload: SearchSessionViewRequest,
    ) -> SearchSessionViewResponse:
        return SearchSessionViewResponse(
            sortBy=payload.sort_by,
            excludeDirectTrainCodesInTransferRoutes=(
                payload.exclude_direct_train_codes_in_transfer_routes
            ),
            displayTrainTypes=sorted(
                {
                    item.strip().upper()
                    for item in payload.display_train_types
                    if item.strip()
                }
            ),
            transferCounts=sorted({count for count in payload.transfer_counts if count >= 0}),
            page=payload.page,
            pageSize=payload.page_size,
            includeTickets=payload.include_tickets,
        )

    def _apply_prices_from_map(
        self,
        route: RouteResponse,
        price_map: dict[str, PriceCacheEntry],
    ) -> RouteResponse:
        """Apply cached prices from the price map to a route's train segments."""
        next_segs = []
        statuses: list[str] = []
        for segment in route.segs:
            if not isinstance(segment, RouteTrainSegmentResponse):
                next_segs.append(segment)
                continue

            key = price_map_key(segment.trainNo, segment.origin.name, segment.destination.name)
            entry = price_map.get(key)
            if entry is None or entry.failed:
                next_segs.append(
                    segment.model_copy(update={"ticketStatus": "unavailable", "seats": []})
                )
                statuses.append("unavailable")
                continue

            seats = self._build_seats_from_entry(entry)
            next_segs.append(
                segment.model_copy(
                    update={
                        "ticketStatus": "ready",
                        "seats": seats,
                    }
                )
            )
            statuses.append("ready")

        route_status = self._derive_route_status(statuses)
        return route.model_copy(update={"segs": next_segs, "ticketStatus": route_status})

    def _build_seats_from_entry(self, entry: PriceCacheEntry) -> list[RouteSeatResponse]:
        """Build sorted seat responses from a PriceCacheEntry."""
        seats = [
            RouteSeatResponse(
                type=seat.seat_type,
                label=SEAT_LABELS.get(seat.seat_type.strip().lower(), seat.seat_type.upper()),
                price=seat.price,
                available=seat.available,
                availabilityText=seat.status or None,
            )
            for seat in entry.seats
        ]
        return sorted(seats, key=lambda item: self._seat_order(item.type))

    def _mark_route_disabled(self, route: RouteResponse) -> RouteResponse:
        """Mark all train segments in a route as disabled with empty seats."""
        next_segs = [
            segment.model_copy(update={"ticketStatus": "disabled", "seats": []})
            if isinstance(segment, RouteTrainSegmentResponse)
            else segment
            for segment in route.segs
        ]
        return route.model_copy(update={"segs": next_segs, "ticketStatus": "disabled"})

    def _derive_route_status(self, statuses: list[str]) -> str:
        if not statuses:
            return "disabled"
        unique_statuses = set(statuses)
        if unique_statuses == {"ready"}:
            return "ready"
        if "ready" in unique_statuses:
            return "partial"
        if unique_statuses == {"disabled"}:
            return "disabled"
        return "unavailable"

    def _seat_order(self, seat_type: str) -> int:
        order = {
            "swz": 0, "tz": 1, "zy": 2, "ze": 3,
            "gr": 4, "rw": 5, "yw": 6, "yz": 7,
            "wz": 8, "gg": 9,
        }
        return order.get(seat_type.strip().lower(), len(order))

    def _sort_key(
        self,
        candidate: CachedRouteCandidate,
        sort_by: str,
        price_map: dict[str, PriceCacheEntry] | None = None,
    ) -> tuple[float, float, int, str, str]:
        if price_map is None:
            price_map = {}

        if sort_by == "price":
            total_price = 0.0
            all_priced = True
            for seg in candidate.segs:
                if not isinstance(seg, CachedTrainSegment) or isinstance(
                    seg, RouteTransferSegmentResponse
                ):
                    continue
                key = price_map_key(seg.trainNo, seg.origin.name, seg.destination.name)
                entry = price_map.get(key)
                if entry is None or entry.min_price is None or entry.failed:
                    all_priced = False
                    break
                total_price += entry.min_price
            if not all_priced:
                total_price = float("inf")
            return (
                total_price,
                float(candidate.transferCount),
                candidate.durationMinutes,
                candidate.departureTime,
                candidate.arrivalTime,
            )

        if sort_by == "departure":
            primary = float(self._time_to_minutes(candidate.departureTime))
        else:
            primary = float(candidate.durationMinutes)
        return (
            float(candidate.transferCount),
            primary,
            candidate.durationMinutes,
            candidate.departureTime,
            candidate.arrivalTime,
        )

    def _time_to_minutes(self, value: str) -> int:
        hours, minutes = value.split(":", maxsplit=1)
        return int(hours) * 60 + int(minutes)

    def _redis_key(self, search_id: str) -> str:
        return f"journey_search:session:{search_id}"
