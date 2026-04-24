from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from redis.asyncio import Redis

from app.integrations.ticket_12306.client import AbstractTicketClient
from app.integrations.ticket_12306.models import TicketSegmentData
from app.integrations.ticket_12306.parser import build_seat_infos, segment_min_price
from app.journey_search_sessions.schemas import (
    CachedRouteCandidate,
    CachedTrainSegment,
    PriceCacheEntry,
    RouteResponse,
    RouteSeatResponse,
    RouteTrainSegmentResponse,
    RouteTransferSegmentResponse,
    SeatInfoEntry,
    price_map_key,
)
from app.models import SeatInfo, SeatLookupKey
from app.railway.repository import StationRepository

logger = logging.getLogger(__name__)

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
        cache_ttl_seconds: int = 600,
        failure_ttl_seconds: int = 10,
    ) -> None:
        self._redis = redis_client
        self._station_repo = station_repo
        self._ticket_client = ticket_client
        self._cache_ttl_seconds = cache_ttl_seconds
        self._failure_ttl_seconds = failure_ttl_seconds

    async def prefetch_all_prices(
        self,
        *,
        run_date: str,
        candidates: list[CachedRouteCandidate],
        max_concurrency: int = 5,
    ) -> dict[str, PriceCacheEntry]:
        """Prefetch ticket prices for all unique legs across all candidates.

        Returns a price map keyed by ``"train_no:from_station:to_station"``.
        """
        if self._ticket_client is None:
            return {}

        # 1. Extract all CachedTrainSegment instances from candidates
        all_segments: list[CachedTrainSegment] = [
            seg
            for candidate in candidates
            for seg in candidate.segs
            if isinstance(seg, CachedTrainSegment)
            and not isinstance(seg, RouteTransferSegmentResponse)
        ]
        if not all_segments:
            return {}

        # 2. Collect all unique station names and resolve telecodes
        station_names: set[str] = set()
        for seg in all_segments:
            station_names.add(seg.origin.name)
            station_names.add(seg.destination.name)
        telecodes = await self._station_repo.get_telecodes_by_names(station_names)

        # 3. Build segment lookup info and check per-segment Redis cache
        #    Each segment is identified by (train_no, from_station, to_station)
        segment_keys: dict[tuple[str, str, str], CachedTrainSegment] = {}
        for seg in all_segments:
            key = (seg.trainNo, seg.origin.name, seg.destination.name)
            if key not in segment_keys:
                segment_keys[key] = seg

        # Load cached rows for all segments
        cached_data: dict[tuple[str, str, str], TicketSegmentData] = {}
        cache_key_map: dict[str, tuple[str, str, str]] = {}
        for seg_key, seg in segment_keys.items():
            redis_key = self._cache_key_for_segment(run_date, seg, telecodes)
            if redis_key:
                cache_key_map[redis_key] = seg_key

        if cache_key_map:
            values = await self._redis.mget(list(cache_key_map.keys()))
            for redis_key, raw in zip(cache_key_map.keys(), values, strict=False):
                if raw is None:
                    continue
                try:
                    payload = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    continue
                if not payload.get("ok"):
                    continue
                seg_key = cache_key_map[redis_key]
                cached_data[seg_key] = TicketSegmentData(
                    seats=[SeatInfo(**seat) for seat in payload["data"]["seats"]],
                    min_price=payload["data"]["min_price"],
                    matched_by=payload["data"]["matched_by"],
                )

        # 4. Determine which segments are uncached
        uncached_seg_keys = {
            seg_key for seg_key in segment_keys if seg_key not in cached_data
        }

        # 5. Group uncached segments by unique leg (from_station, to_station)
        #    and collect which segment keys belong to each leg
        legs_segments: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
        for seg_key in uncached_seg_keys:
            _train_no, from_station, to_station = seg_key
            leg = (from_station, to_station)
            legs_segments.setdefault(leg, []).append(seg_key)

        # Build the list of legs to fetch with their telecodes
        legs_to_fetch: list[tuple[tuple[str, str], str, str]] = []
        for leg_key in legs_segments:
            from_station, to_station = leg_key
            from_code = telecodes.get(from_station)
            to_code = telecodes.get(to_station)
            if from_code and to_code:
                legs_to_fetch.append((leg_key, from_code, to_code))

        # 6. Fetch uncached legs concurrently
        fetched_legs: dict[tuple[str, str], dict[str, Any]] = {}
        if legs_to_fetch:
            semaphore = asyncio.Semaphore(max_concurrency)

            async def fetch_one_leg(
                leg_key: tuple[str, str], from_code: str, to_code: str
            ) -> tuple[tuple[str, str], dict[str, Any]]:
                async with semaphore:
                    try:
                        return leg_key, await self._ticket_client.fetch_leg(  # type: ignore[union-attr]
                            run_date, from_code, to_code
                        )
                    except Exception as exc:
                        logger.warning(
                            "Prefetch failed for leg %s→%s: %s",
                            leg_key[0],
                            leg_key[1],
                            exc,
                        )
                        return leg_key, {}

            results = await asyncio.gather(
                *(
                    fetch_one_leg(leg_key, from_code, to_code)
                    for leg_key, from_code, to_code in legs_to_fetch
                )
            )
            for leg_key, rows in results:
                fetched_legs[leg_key] = rows

        # 7. Extract ticket data for each uncached segment from fetched legs
        fetched_data: dict[tuple[str, str, str], TicketSegmentData] = {}
        for seg_key in uncached_seg_keys:
            train_no, from_station, to_station = seg_key
            leg = (from_station, to_station)
            rows = fetched_legs.get(leg, {})
            if not rows:
                continue

            # Match by train_no first, then by station_train_code
            row = rows.get(train_no)
            matched_by = "train_no"
            if row is None:
                seg = segment_keys[seg_key]
                stc = seg.no
                row = rows.get(stc)
                matched_by = "station_train_code"

            if row is None:
                continue

            seat_status, seat_prices = row
            seats = build_seat_infos(seat_status, seat_prices)
            fetched_data[seg_key] = TicketSegmentData(
                seats=seats,
                min_price=segment_min_price(seats),
                matched_by=matched_by,
            )

        # 8. Store fetched results in per-segment Redis cache
        for seg_key in uncached_seg_keys:
            seg = segment_keys[seg_key]
            redis_key = self._cache_key_for_segment(run_date, seg, telecodes)
            if not redis_key:
                continue
            ticket = fetched_data.get(seg_key)
            if ticket is None:
                payload: dict[str, Any] = {"ok": False}
                ttl = self._failure_ttl_seconds
            else:
                payload = {"ok": True, "data": asdict(ticket)}
                ttl = self._cache_ttl_seconds
            try:
                await self._redis.setex(
                    redis_key, ttl, json.dumps(payload, ensure_ascii=False)
                )
            except Exception as exc:
                logger.warning(
                    "Failed to write segment cache for %s: %s", redis_key, exc
                )

        # 9. Build and return the complete price map
        all_data = dict(cached_data)
        all_data.update(fetched_data)

        price_map: dict[str, PriceCacheEntry] = {}
        for seg_key, seg in segment_keys.items():
            train_no, from_station, to_station = seg_key
            map_key = price_map_key(train_no, from_station, to_station)
            ticket = all_data.get(seg_key)
            if ticket is not None:
                price_map[map_key] = PriceCacheEntry(
                    min_price=ticket.min_price,
                    seats=[
                        SeatInfoEntry(
                            seat_type=s.seat_type,
                            status=s.status,
                            price=s.price,
                            available=s.available,
                        )
                        for s in ticket.seats
                    ],
                    matched_by=ticket.matched_by,
                    failed=False,
                )
            else:
                price_map[map_key] = PriceCacheEntry(failed=True)

        return price_map

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
