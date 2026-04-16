from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict

from redis.asyncio import Redis

from app.integrations.ticket_12306.client import AbstractTicketClient
from app.integrations.ticket_12306.models import TicketSegmentData
from app.journey_search_sessions.schemas import (
    CachedTrainSegment,
    RouteResponse,
    RouteSeatResponse,
    RouteTrainSegmentResponse,
)
from app.models import SeatInfo, SeatLookupKey
from app.railway.repository import StationRepository

SEAT_LABELS: dict[str, str] = {
    "swz": "商务座",
    "tz": "特等座",
    "zy": "一等座",
    "ze": "二等座",
    "gr": "高级软卧",
    "rw": "软卧",
    "yw": "硬卧",
    "yz": "硬座",
    "wz": "无座",
    "gg": "其他",
}


class Ticket12306Service:
    def __init__(
        self,
        redis_client: Redis,
        station_repo: StationRepository,
        ticket_client: AbstractTicketClient | None,
        cache_ttl_seconds: int = 60,
        failure_ttl_seconds: int = 10,
    ) -> None:
        self._redis = redis_client
        self._station_repo = station_repo
        self._ticket_client = ticket_client
        self._cache_ttl_seconds = cache_ttl_seconds
        self._failure_ttl_seconds = failure_ttl_seconds

    async def enrich_routes_for_view(
        self,
        *,
        run_date: str,
        routes: list[RouteResponse],
    ) -> list[RouteResponse]:
        if not routes:
            return routes

        if self._ticket_client is None:
            return [self._mark_route_disabled(route) for route in routes]

        segments = self._collect_train_segments(routes)
        if not segments:
            return routes

        telecodes = await self._station_repo.get_telecodes_by_names(
            {segment.origin.name for segment in segments}
            | {segment.destination.name for segment in segments}
        )

        cached_rows = await self._load_cached_rows(
            run_date=run_date,
            segments=segments,
            telecodes=telecodes,
        )
        missing_route_segments = [
            segment
            for segment in segments
            if (segment.trainNo, segment.origin.name, segment.destination.name)
            not in cached_rows
        ]
        missing_segments = {
            (segment.trainNo, segment.origin.name, segment.destination.name)
            for segment in missing_route_segments
        }

        fetched: dict[SeatLookupKey, TicketSegmentData] = {}
        if missing_segments:
            train_codes = {
                (segment.trainNo, segment.origin.name, segment.destination.name): segment.no
                for segment in missing_route_segments
            }
            fetched = await self._ticket_client.fetch_tickets(
                run_date=run_date,
                segments=missing_segments,
                telecodes=telecodes,
                train_codes=train_codes,
            )
            await self._store_segment_cache(
                run_date=run_date,
                segments=missing_route_segments,
                telecodes=telecodes,
                fetched=fetched,
            )

        ticket_map = dict(cached_rows)
        ticket_map.update(fetched)
        return [self._merge_route_tickets(route, ticket_map) for route in routes]

    def _collect_train_segments(self, routes: Iterable[RouteResponse]) -> list[RouteTrainSegmentResponse]:
        return [
            segment
            for route in routes
            for segment in route.segs
            if isinstance(segment, RouteTrainSegmentResponse)
        ]

    async def _load_cached_rows(
        self,
        *,
        run_date: str,
        segments: list[RouteTrainSegmentResponse],
        telecodes: dict[str, str],
    ) -> dict[SeatLookupKey, TicketSegmentData]:
        result: dict[SeatLookupKey, TicketSegmentData] = {}
        cache_keys = {
            self._cache_key_for_segment(run_date, segment, telecodes): segment
            for segment in segments
        }
        valid_keys = {key: segment for key, segment in cache_keys.items() if key}
        if not valid_keys:
            return result

        values = await self._redis.mget(list(valid_keys.keys()))
        for cache_key, raw in zip(valid_keys.keys(), values, strict=False):
            if raw is None:
                continue
            payload = json.loads(raw)
            if not payload.get("ok"):
                continue
            segment = valid_keys[cache_key]
            lookup_key = (segment.trainNo, segment.origin.name, segment.destination.name)
            result[lookup_key] = TicketSegmentData(
                seats=[SeatInfo(**seat) for seat in payload["data"]["seats"]],
                min_price=payload["data"]["min_price"],
                matched_by=payload["data"]["matched_by"],
            )
        return result

    async def _store_segment_cache(
        self,
        *,
        run_date: str,
        segments: list[RouteTrainSegmentResponse],
        telecodes: dict[str, str],
        fetched: dict[SeatLookupKey, TicketSegmentData],
    ) -> None:
        for segment in segments:
            cache_key = self._cache_key_for_segment(run_date, segment, telecodes)
            if not cache_key:
                continue
            lookup_key = (segment.trainNo, segment.origin.name, segment.destination.name)
            ticket = fetched.get(lookup_key)
            if ticket is None:
                payload = {"ok": False}
                ttl = self._failure_ttl_seconds
            else:
                payload = {"ok": True, "data": asdict(ticket)}
                ttl = self._cache_ttl_seconds
            await self._redis.setex(cache_key, ttl, json.dumps(payload, ensure_ascii=False))

    def _merge_route_tickets(
        self,
        route: RouteResponse,
        ticket_map: dict[SeatLookupKey, TicketSegmentData],
    ) -> RouteResponse:
        next_segs = []
        statuses: list[str] = []
        for segment in route.segs:
            if not isinstance(segment, RouteTrainSegmentResponse):
                next_segs.append(segment)
                continue

            lookup_key = (segment.trainNo, segment.origin.name, segment.destination.name)
            ticket = ticket_map.get(lookup_key)
            if ticket is None:
                next_segs.append(segment.model_copy(update={"ticketStatus": "unavailable", "seats": []}))
                statuses.append("unavailable")
                continue

            seats = self._build_route_seats(ticket)
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

    def _mark_route_disabled(self, route: RouteResponse) -> RouteResponse:
        next_segs = [
            segment.model_copy(update={"ticketStatus": "disabled", "seats": []})
            if isinstance(segment, RouteTrainSegmentResponse)
            else segment
            for segment in route.segs
        ]
        return route.model_copy(update={"segs": next_segs, "ticketStatus": "disabled"})

    def _derive_route_status(self, statuses: list[str]) -> Literal["ready", "partial", "unavailable", "disabled"]:
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

    def _build_route_seats(self, ticket: TicketSegmentData) -> list[RouteSeatResponse]:
        seats = [
            RouteSeatResponse(
                type=seat.seat_type,
                label=SEAT_LABELS.get(seat.seat_type.strip().lower(), seat.seat_type.upper()),
                price=seat.price,
                available=seat.available,
                availabilityText=seat.status or None,
            )
            for seat in ticket.seats
        ]
        return sorted(
            seats,
            key=lambda item: self._seat_order(item.type),
        )

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

    def _cache_key_for_segment(
        self,
        run_date: str,
        segment: CachedTrainSegment | RouteTrainSegmentResponse,
        telecodes: dict[str, str],
    ) -> str | None:
        from_code = telecodes.get(segment.origin.name)
        to_code = telecodes.get(segment.destination.name)
        if not from_code or not to_code:
            return None
        return (
            f"journey_search:ticket_segment:{run_date}:{segment.trainNo}:"
            f"{from_code}:{to_code}"
        )
