from __future__ import annotations

import base64
import json
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, cast
from uuid import UUID

from app.exceptions import BusinessError, NotFoundError
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
from app.journeys.schemas import JourneyResult, JourneySearchRequest, JourneySearchResponse
from app.journeys.service import JourneyService
from app.railway.repository import StationRepository
from app.route_plan_cache.repository import (
    RoutePlanAvailableFacets,
    RoutePlanQueryFilters,
    RoutePlanRepository,
    RoutePlanViewQuery,
)


def _get_train_type(train_code: str) -> str:
    code = train_code.strip().upper()
    prefix = ""
    for character in code:
        if not character.isalpha():
            break
        prefix += character
    return prefix


def _time_to_minutes(value: str) -> int:
    hours, minutes = value.split(":", maxsplit=1)
    return int(hours) * 60 + int(minutes)


def _request_time_to_minutes(value: time | None) -> int | None:
    if value is None:
        return None
    return value.hour * 60 + value.minute


def _arrival_deadline_to_abs_min(value: time | None) -> int | None:
    if value is None:
        return None
    minutes = value.hour * 60 + value.minute
    return 1440 + minutes if minutes < 360 else minutes


def _effective_max_transfer_minutes(value: int | None) -> int | None:
    if value is None or value <= 0:
        return None
    return value


def _encode_search_context(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_search_context(search_id: str) -> dict[str, Any]:
    try:
        padded = search_id + ("=" * (-len(search_id) % 4))
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise NotFoundError("搜索方案池不存在或已过期") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("planIds"), list):
        raise NotFoundError("搜索方案池不存在或已过期")
    if not all(isinstance(plan_id, str) for plan_id in payload["planIds"]):
        raise NotFoundError("搜索方案池不存在或已过期")
    try:
        [UUID(plan_id) for plan_id in payload["planIds"]]
    except ValueError as exc:
        raise NotFoundError("搜索方案池不存在或已过期") from exc
    return payload


def _is_no_routes_found_error(exc: BusinessError) -> bool:
    return exc.http_status == 404 and "未找到" in exc.message and "路线" in exc.message


class JourneySearchSessionService:
    def __init__(
        self,
        ttl_seconds: int,
        journey_service: JourneyService,
        station_repo: StationRepository,
        ticket_service: Ticket12306Service,
        route_plan_repo: RoutePlanRepository,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._journey_service = journey_service
        self._station_repo = station_repo
        self._ticket_service = ticket_service
        self._route_plan_repo = route_plan_repo

    async def create_session(
        self,
        payload: SearchSessionCreateRequest,
    ) -> SearchSessionCreateResponse:
        from_station = payload.from_station.strip()
        to_station = payload.to_station.strip()
        transfer_counts = self._requested_transfer_counts(payload)
        expires_at = datetime.now(UTC) + timedelta(seconds=self._ttl_seconds)

        plans = [
            await self._ensure_plan(
                from_station=from_station,
                to_station=to_station,
                search_date=payload.date,
                transfer_count=transfer_count,
                expires_at=expires_at,
            )
            for transfer_count in transfer_counts
        ]
        plan_ids = [str(plan["plan_id"]) for plan in plans]
        response_expires_at = self._plans_expires_at(plans)
        base_filters = self._query_filters_from_payload(payload)
        search_id = _encode_search_context(
            {
                "planIds": plan_ids,
                "fromStation": from_station,
                "toStation": to_station,
                "date": payload.date.isoformat(),
                "filters": self._search_filters_to_context(payload),
            }
        )
        total_candidates = await self._route_plan_repo.count_candidates(
            plan_ids,
            base_filters,
        )

        summary = SearchSummaryResponse(
            fromStation=from_station,
            toStation=to_station,
            date=payload.date.isoformat(),
            totalCandidates=total_candidates,
        )
        view_request = payload.view or SearchSessionViewRequest()
        view_result = await self._build_view_result(
            plan_ids,
            base_filters,
            payload.date.isoformat(),
            view_request,
        )
        return SearchSessionCreateResponse(
            searchId=search_id,
            expiresAt=response_expires_at,
            searchSummary=summary,
            viewResult=view_result,
        )

    async def get_summary(self, search_id: str) -> SearchSessionSummaryResponse:
        context = await self._load_context(search_id)
        base_filters = self._query_filters_from_context(context)
        total_candidates = await self._route_plan_repo.count_candidates(
            context["planIds"],
            base_filters,
        )
        expires_at = self._context_expires_at(context)
        return SearchSessionSummaryResponse(
            searchId=search_id,
            expiresAt=expires_at,
            searchSummary=SearchSummaryResponse(
                fromStation=str(context["fromStation"]),
                toStation=str(context["toStation"]),
                date=str(context["date"]),
                totalCandidates=total_candidates,
            ),
        )

    async def get_view(
        self,
        search_id: str,
        payload: SearchSessionViewRequest,
    ) -> SearchSessionViewResultResponse:
        context = await self._load_context(search_id)
        base_filters = self._query_filters_from_context(context)
        return await self._build_view_result(
            context["planIds"],
            base_filters,
            str(context["date"]),
            payload,
        )

    async def delete_session(self, search_id: str) -> SearchSessionDeleteResponse:
        _decode_search_context(search_id)
        return SearchSessionDeleteResponse(deleted=True)

    async def _ensure_plan(
        self,
        *,
        from_station: str,
        to_station: str,
        search_date: date,
        transfer_count: int,
        expires_at: datetime,
    ) -> dict[str, Any]:
        existing = await self._route_plan_repo.find_ready_plan(
            from_station=from_station,
            to_station=to_station,
            search_date=search_date,
            transfer_count=transfer_count,
        )
        if existing is not None:
            return existing

        search_request = JourneySearchRequest(
            from_station=from_station,
            to_station=to_station,
            date=search_date,
            transfer_count=transfer_count,
            include_fewer_transfers=False,
            min_transfer_minutes=0,
            max_transfer_minutes=None,
            filter_running_only=True,
            sort_by="duration",
            train_sequence_top_n=0,
            exclude_direct_train_codes_in_transfer_routes=False,
        ).model_copy(update={"display_limit": 0})
        try:
            search_response = await self._journey_service.search(
                search_request
            )
        except BusinessError as exc:
            if not _is_no_routes_found_error(exc):
                raise
            candidates = []
        else:
            candidates = [
                candidate
                for candidate in await self._build_candidates(search_response)
                if candidate.transferCount == transfer_count
            ]
        candidates.sort(key=lambda candidate: self._sort_key(candidate, "duration"))
        return await self._route_plan_repo.replace_plan(
            from_station=from_station,
            to_station=to_station,
            search_date=search_date,
            transfer_count=transfer_count,
            expires_at=expires_at,
            candidates=candidates,
        )

    async def _load_context(self, search_id: str) -> dict[str, Any]:
        context = _decode_search_context(search_id)
        plans = await self._route_plan_repo.get_plans_by_ids(
            [str(plan_id) for plan_id in context["planIds"]]
        )
        if len(plans) != len(context["planIds"]):
            raise NotFoundError("搜索方案池不存在或已过期")
        context["plans"] = plans
        return context

    def _context_expires_at(self, context: dict[str, Any]) -> datetime:
        plans = context.get("plans")
        if not isinstance(plans, list) or not plans:
            raise NotFoundError("搜索方案池不存在或已过期")
        return self._plans_expires_at(cast(list[dict[str, Any]], plans))

    def _plans_expires_at(self, plans: list[dict[str, Any]]) -> datetime:
        if not plans:
            raise NotFoundError("搜索方案池不存在或已过期")
        return min(cast(datetime, plan["expires_at"]) for plan in plans)

    def _requested_transfer_counts(self, payload: SearchSessionCreateRequest) -> list[int]:
        if payload.include_fewer_transfers:
            return list(range(0, payload.transfer_count + 1))
        return [payload.transfer_count]

    def _search_filters_to_context(
        self,
        payload: SearchSessionCreateRequest,
    ) -> dict[str, Any]:
        return {
            "allowedTrainTypes": payload.allowed_train_types,
            "excludedTrainTypes": payload.excluded_train_types,
            "allowedTrains": payload.allowed_trains,
            "excludedTrains": payload.excluded_trains,
            "departureTimeStart": (
                payload.departure_time_start.isoformat(timespec="minutes")
                if payload.departure_time_start
                else None
            ),
            "departureTimeEnd": (
                payload.departure_time_end.isoformat(timespec="minutes")
                if payload.departure_time_end
                else None
            ),
            "arrivalDeadline": (
                payload.arrival_deadline.isoformat(timespec="minutes")
                if payload.arrival_deadline
                else None
            ),
            "minTransferMinutes": payload.min_transfer_minutes,
            "maxTransferMinutes": payload.max_transfer_minutes,
            "allowedTransferStations": payload.allowed_transfer_stations,
            "excludedTransferStations": payload.excluded_transfer_stations,
        }

    def _query_filters_from_context(
        self,
        context: dict[str, Any],
    ) -> RoutePlanQueryFilters:
        filters = context.get("filters")
        if not isinstance(filters, dict):
            return RoutePlanQueryFilters()
        return RoutePlanQueryFilters(
            allowed_train_types=frozenset({
                str(item).strip().upper()
                for item in filters.get("allowedTrainTypes", [])
                if str(item).strip()
            }),
            excluded_train_types=frozenset({
                str(item).strip().upper()
                for item in filters.get("excludedTrainTypes", [])
                if str(item).strip()
            }),
            allowed_trains=frozenset({
                str(item).strip().upper()
                for item in filters.get("allowedTrains", [])
                if str(item).strip()
            }),
            excluded_trains=frozenset({
                str(item).strip().upper()
                for item in filters.get("excludedTrains", [])
                if str(item).strip()
            }),
            departure_time_start_min=self._context_time_to_minutes(
                filters.get("departureTimeStart")
            ),
            departure_time_end_min=self._context_time_to_minutes(
                filters.get("departureTimeEnd")
            ),
            arrival_deadline_abs_min=self._context_arrival_deadline(
                filters.get("arrivalDeadline")
            ),
            min_transfer_minutes=int(filters.get("minTransferMinutes", 0) or 0),
            max_transfer_minutes=_effective_max_transfer_minutes(
                int(filters["maxTransferMinutes"])
                if filters.get("maxTransferMinutes") is not None
                else None
            ),
            allowed_transfer_stations=frozenset({
                str(item).strip()
                for item in filters.get("allowedTransferStations", [])
                if str(item).strip()
            }),
            excluded_transfer_stations=frozenset({
                str(item).strip()
                for item in filters.get("excludedTransferStations", [])
                if str(item).strip()
            }),
        )

    def _query_filters_from_payload(
        self,
        payload: SearchSessionCreateRequest,
    ) -> RoutePlanQueryFilters:
        return RoutePlanQueryFilters(
            allowed_train_types=frozenset({
                item.strip().upper() for item in payload.allowed_train_types if item.strip()
            }),
            excluded_train_types=frozenset({
                item.strip().upper() for item in payload.excluded_train_types if item.strip()
            }),
            allowed_trains=frozenset({
                item.strip().upper() for item in payload.allowed_trains if item.strip()
            }),
            excluded_trains=frozenset({
                item.strip().upper() for item in payload.excluded_trains if item.strip()
            }),
            departure_time_start_min=_request_time_to_minutes(payload.departure_time_start),
            departure_time_end_min=_request_time_to_minutes(payload.departure_time_end),
            arrival_deadline_abs_min=_arrival_deadline_to_abs_min(payload.arrival_deadline),
            min_transfer_minutes=payload.min_transfer_minutes,
            max_transfer_minutes=_effective_max_transfer_minutes(
                payload.max_transfer_minutes
            ),
            allowed_transfer_stations=frozenset({
                item.strip() for item in payload.allowed_transfer_stations if item.strip()
            }),
            excluded_transfer_stations=frozenset({
                item.strip() for item in payload.excluded_transfer_stations if item.strip()
            }),
        )

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
        transfer_count = max(len(journey.segments) - 1, 0)
        return CachedRouteCandidate(
            id=journey.id,
            trainNo=" / ".join(segment.train_code for segment in journey.segments),
            type="直达" if journey.is_direct else f"中转 {transfer_count} 次",
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
            transferCount=transfer_count,
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
        plan_ids: list[str],
        filters: RoutePlanQueryFilters,
        run_date: str,
        payload: SearchSessionViewRequest,
        price_map: dict[str, PriceCacheEntry] | None = None,
    ) -> SearchSessionViewResultResponse:
        if price_map is None:
            price_map = {}

        applied_view = self._build_applied_view(payload)
        query_result = await self._route_plan_repo.query_view(
            plan_ids,
            RoutePlanViewQuery(
                filters=filters,
                sort_by=payload.sort_by,
                page=payload.page,
                page_size=payload.page_size,
                transfer_counts=frozenset(applied_view.transferCounts),
                display_train_types=frozenset(applied_view.displayTrainTypes),
                exclude_direct_train_codes_in_transfer_routes=(
                    payload.exclude_direct_train_codes_in_transfer_routes
                ),
            ),
        )
        items = [self._to_route_response(candidate) for candidate in query_result.candidates]

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
            total=query_result.total,
            view=applied_view,
            facets=self._facets_to_response(query_result.facets),
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

    def _facets_to_response(
        self,
        facets: RoutePlanAvailableFacets,
    ) -> SearchSessionAvailableFacetsResponse:
        return SearchSessionAvailableFacetsResponse(
            transferCounts=facets.transfer_counts,
            trainTypes=facets.train_types,
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
            transferCounts=sorted({
                count
                for count in payload.transfer_counts
                if 0 <= count <= 3
            }),
            page=payload.page,
            pageSize=payload.page_size,
            includeTickets=payload.include_tickets,
        )

    def _apply_prices_from_map(
        self,
        route: RouteResponse,
        price_map: dict[str, PriceCacheEntry],
    ) -> RouteResponse:
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
            "swz": 0,
            "tz": 1,
            "zy": 2,
            "ze": 3,
            "gr": 4,
            "rw": 5,
            "yw": 6,
            "yz": 7,
            "wz": 8,
            "gg": 9,
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

        if sort_by == "price" and price_map:
            total_price = 0.0
            all_priced = True
            for segment in self._train_segments(candidate):
                key = price_map_key(
                    segment.trainNo,
                    segment.origin.name,
                    segment.destination.name,
                )
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
            primary = float(_time_to_minutes(candidate.departureTime))
        else:
            primary = float(candidate.durationMinutes)
        return (
            float(candidate.transferCount),
            primary,
            candidate.durationMinutes,
            candidate.departureTime,
            candidate.arrivalTime,
        )

    def _train_segments(self, candidate: CachedRouteCandidate) -> list[CachedTrainSegment]:
        return [
            segment
            for segment in candidate.segs
            if isinstance(segment, CachedTrainSegment)
            and not isinstance(segment, RouteTransferSegmentResponse)
        ]

    def _context_time_to_minutes(self, value: object) -> int | None:
        if not isinstance(value, str) or not value:
            return None
        return _time_to_minutes(value)

    def _context_arrival_deadline(self, value: object) -> int | None:
        if not isinstance(value, str) or not value:
            return None
        minutes = _time_to_minutes(value)
        return 1440 + minutes if minutes < 360 else minutes
