from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, Literal

from redis.asyncio import Redis

from app.integrations.ticket_12306.browser_manager import PlaywrightUnavailableError
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
from app.models import SeatInfo
from app.railway.repository import StationRepository

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[dict[str, Any]], Awaitable[None] | None]
SegmentLookupKey = tuple[str, str, str, str]
LegLookupKey = tuple[str, str, str]
OnLegCompleteCallback = Callable[[dict[str, PriceCacheEntry]], Awaitable[None] | None]

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
        max_concurrency: int = 2,
        on_progress: ProgressCallback | None = None,
        on_leg_complete: OnLegCompleteCallback | None = None,
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
        segment_keys: dict[SegmentLookupKey, CachedTrainSegment] = {}
        for seg in all_segments:
            key = self._segment_lookup_key(seg)
            if key not in segment_keys:
                segment_keys[key] = seg

        # Load cached rows for all segments
        cached_data: dict[SegmentLookupKey, TicketSegmentData] = {}
        legs_segments: dict[LegLookupKey, list[SegmentLookupKey]] = {}
        for seg_key in segment_keys:
            departure_date, _train_no, from_station, to_station = seg_key
            leg = (departure_date, from_station, to_station)
            legs_segments.setdefault(leg, []).append(seg_key)

        resolved_legs: set[LegLookupKey] = set()
        cache_key_map: dict[str, LegLookupKey] = {}
        for leg_key in legs_segments:
            redis_key = self._cache_key_for_leg_key(leg_key, telecodes)
            if redis_key:
                cache_key_map[redis_key] = leg_key

        if cache_key_map:
            values = await self._redis.mget(list(cache_key_map.keys()))
            for redis_key, raw in zip(cache_key_map.keys(), values, strict=False):
                if raw is None:
                    continue
                leg_key = cache_key_map[redis_key]
                if self._is_failure_cache_value(raw):
                    resolved_legs.add(leg_key)
                    continue
                try:
                    payload = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    continue
                if not isinstance(payload, dict):
                    continue
                resolved_legs.add(leg_key)
                for seg_key in legs_segments[leg_key]:
                    segment = segment_keys[seg_key]
                    ticket = self._ticket_from_leg_payload(payload, segment)
                    if ticket is not None:
                        cached_data[seg_key] = ticket
        # 3b. Invoke on_leg_complete for cached legs
        if on_leg_complete and cached_data:
            cached_leg_prices: dict[str, PriceCacheEntry] = {}
            for cached_sk, ticket in cached_data.items():
                pmk = price_map_key(cached_sk[1], cached_sk[2], cached_sk[3])
                cached_leg_prices[pmk] = self._ticket_to_price_entry(ticket)
            if cached_leg_prices:
                maybe = on_leg_complete(cached_leg_prices)
                if maybe is not None:
                    await maybe

        # 4. Determine which segments are uncached
        uncached_leg_keys = {leg for leg in legs_segments if leg not in resolved_legs}
        uncached_seg_keys = {
            seg_key
            for leg in uncached_leg_keys
            for seg_key in legs_segments.get(leg, [])
        }

        # Build the list of legs to fetch with their telecodes
        legs_to_fetch: list[tuple[LegLookupKey, str, str]] = []
        for leg_key in uncached_leg_keys:
            _departure_date, from_station, to_station = leg_key
            from_code = telecodes.get(from_station)
            to_code = telecodes.get(to_station)
            if from_code and to_code:
                legs_to_fetch.append((leg_key, from_code, to_code))

        # 5b. Emit pricing progress start
        total_legs = len(legs_segments)
        cached_legs = len(resolved_legs)
        legs_to_fetch_count = len(legs_to_fetch)
        if on_progress:
            maybe = on_progress({
                "type": "pricing_started",
                "totalLegs": total_legs,
                "cachedLegs": cached_legs,
                "legsToFetch": legs_to_fetch_count,
            })
            if maybe is not None:
                await maybe

        # 6. Fetch uncached legs concurrently
        fetched_legs: dict[LegLookupKey, dict[str, Any]] = {}
        if legs_to_fetch:
            semaphore = asyncio.Semaphore(max_concurrency)
            completed_count = 0

            async def fetch_one_leg(
                leg_key: LegLookupKey, from_code: str, to_code: str
            ) -> tuple[LegLookupKey, dict[str, Any]]:
                nonlocal completed_count
                async with semaphore:
                    try:
                        departure_date, from_station, to_station = leg_key
                        result = leg_key, await self._ticket_client.fetch_leg(  # type: ignore[union-attr]
                            departure_date,
                            from_station,
                            to_station,
                            from_code,
                            to_code,
                        )
                    except PlaywrightUnavailableError:
                        raise
                    except Exception as exc:
                        logger.warning(
                            "Prefetch failed for leg %s→%s: %s",
                            leg_key[0],
                            leg_key[1],
                            exc,
                        )
                        result = leg_key, {}
                    completed_count += 1
                    if on_progress:
                        maybe = on_progress({
                            "type": "leg_fetched",
                            "completed": completed_count,
                            "total": legs_to_fetch_count,
                        })
                        if maybe is not None:
                            await maybe
                    # Invoke per-leg callback with price entries
                    if on_leg_complete:
                        _lk, leg_rows = result
                        leg_price_batch: dict[str, PriceCacheEntry] = {}
                        for sk in legs_segments.get(_lk, []):
                            seg = segment_keys[sk]
                            if not leg_rows:
                                _d, tn, fs, ts = sk
                                key = price_map_key(tn, fs, ts)
                                leg_price_batch[key] = PriceCacheEntry(failed=True)
                            else:
                                ticket = self._ticket_from_rows(
                                    leg_rows,
                                    train_no=seg.trainNo if hasattr(seg, "trainNo") else sk[1],
                                    station_train_code=seg.no if hasattr(seg, "no") else "",
                                )
                                _d, tn, fs, ts = sk
                                mk = price_map_key(tn, fs, ts)
                                if ticket is not None:
                                    leg_price_batch[mk] = PriceCacheEntry(
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
                                    leg_price_batch[mk] = PriceCacheEntry(failed=True)
                        if leg_price_batch:
                            cb_result = on_leg_complete(leg_price_batch)
                            if cb_result is not None:
                                await cb_result
                    return result

            results = await asyncio.gather(
                *(
                    fetch_one_leg(leg_key, from_code, to_code)
                    for leg_key, from_code, to_code in legs_to_fetch
                )
            )
            for leg_key, rows in results:
                fetched_legs[leg_key] = rows

        # 7. Extract ticket data for each uncached segment from fetched legs
        fetched_data: dict[SegmentLookupKey, TicketSegmentData] = {}
        for seg_key in uncached_seg_keys:
            departure_date, train_no, from_station, to_station = seg_key
            leg = (departure_date, from_station, to_station)
            rows = fetched_legs.get(leg, {})
            if not rows:
                continue

            ticket = self._ticket_from_rows(
                rows,
                train_no=train_no,
                station_train_code=segment_keys[seg_key].no,
            )
            if ticket is not None:
                fetched_data[seg_key] = ticket

        # 8. Store cache entries for EVERY train_no found in each fetched leg
        #    response, not only the requested segments. A 12306 leg payload
        #    contains all trains on that physical leg/date; persisting them
        #    means a future search asking about a different train on the same
        #    leg/date hits the cache for free.
        leg_telecodes: dict[LegLookupKey, tuple[str, str]] = {}
        for leg_key, _from_code, _to_code in legs_to_fetch:
            leg_telecodes[leg_key] = (_from_code, _to_code)
        await self._store_fetched_leg_caches(
            fetched_legs=fetched_legs,
            leg_telecodes=leg_telecodes,
        )

        # 9. Build and return the complete price map
        all_data = dict(cached_data)
        all_data.update(fetched_data)

        price_map: dict[str, PriceCacheEntry] = {}
        for seg_key, _seg in segment_keys.items():
            _departure_date, train_no, from_station, to_station = seg_key
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

    async def enrich_routes_cache_only(
        self,
        *,
        run_date: str,
        routes: list[RouteResponse],
    ) -> list[RouteResponse]:
        """Read cached prices from Redis; mark uncached segments as loading."""
        if not routes:
            return routes

        segments = self._collect_train_segments(routes)
        if not segments:
            return routes

        telecodes = await self._station_repo.get_telecodes_by_names(
            {segment.origin.name for segment in segments}
            | {segment.destination.name for segment in segments}
        )

        cached_rows, _resolved_legs = await self._load_cached_rows(
            run_date=run_date,
            segments=segments,
            telecodes=telecodes,
        )

        return [self._merge_route_tickets_cache_only(route, cached_rows) for route in routes]

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

        cached_rows, resolved_cache_legs = await self._load_cached_rows(
            run_date=run_date,
            segments=segments,
            telecodes=telecodes,
        )
        missing_route_segments = [
            segment
            for segment in segments
            if (
                segment.departureDate,
                segment.trainNo,
                segment.origin.name,
                segment.destination.name,
            )
            not in cached_rows
            and (
                segment.departureDate,
                segment.origin.name,
                segment.destination.name,
            )
            not in resolved_cache_legs
        ]
        missing_segments = {
            (
                segment.departureDate,
                segment.trainNo,
                segment.origin.name,
                segment.destination.name,
            )
            for segment in missing_route_segments
        }

        fetched: dict[tuple[str, str, str, str], TicketSegmentData] = {}
        if missing_segments:
            train_codes = {
                (
                    segment.departureDate,
                    segment.trainNo,
                    segment.origin.name,
                    segment.destination.name,
                ): segment.no
                for segment in missing_route_segments
            }
            fetched, fetched_legs, leg_telecodes = await self._fetch_tickets_by_segment_date(
                segments=missing_segments,
                telecodes=telecodes,
                train_codes=train_codes,
            )
            await self._store_fetched_leg_caches(
                fetched_legs=fetched_legs,
                leg_telecodes=leg_telecodes,
            )

        ticket_map = dict(cached_rows)
        ticket_map.update(fetched)
        return [self._merge_route_tickets(route, ticket_map) for route in routes]

    async def _fetch_tickets_by_segment_date(
        self,
        *,
        segments: set[tuple[str, str, str, str]],
        telecodes: dict[str, str],
        train_codes: dict[tuple[str, str, str, str], str],
    ) -> tuple[
        dict[SegmentLookupKey, TicketSegmentData],
        dict[LegLookupKey, dict[str, Any]],
        dict[LegLookupKey, tuple[str, str]],
    ]:
        fetched: dict[SegmentLookupKey, TicketSegmentData] = {}
        by_leg: dict[LegLookupKey, list[SegmentLookupKey]] = {}
        for departure_date, train_no, from_station, to_station in segments:
            leg = (departure_date, from_station, to_station)
            by_leg.setdefault(leg, []).append(
                (departure_date, train_no, from_station, to_station)
            )

        fetched_legs: dict[LegLookupKey, dict[str, Any]] = {}
        leg_telecodes: dict[LegLookupKey, tuple[str, str]] = {}
        for leg_key, leg_segments in by_leg.items():
            departure_date, from_station, to_station = leg_key
            from_code = telecodes.get(from_station)
            to_code = telecodes.get(to_station)
            if not from_code or not to_code:
                fetched_legs[leg_key] = {}
                continue
            leg_telecodes[leg_key] = (from_code, to_code)
            rows = await self._ticket_client.fetch_leg(  # type: ignore[union-attr]
                departure_date,
                from_station,
                to_station,
                from_code,
                to_code,
            )
            fetched_legs[leg_key] = rows
            for seg_key in leg_segments:
                _departure_date, train_no, _from_station, _to_station = seg_key
                ticket = self._ticket_from_rows(
                    rows,
                    train_no=train_no,
                    station_train_code=train_codes[seg_key],
                )
                if ticket is not None:
                    fetched[seg_key] = ticket
        return fetched, fetched_legs, leg_telecodes

    def _collect_train_segments(
        self, routes: Iterable[RouteResponse]
    ) -> list[RouteTrainSegmentResponse]:
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
    ) -> tuple[dict[SegmentLookupKey, TicketSegmentData], set[LegLookupKey]]:
        result: dict[SegmentLookupKey, TicketSegmentData] = {}
        resolved_legs: set[LegLookupKey] = set()
        legs_segments: dict[LegLookupKey, list[RouteTrainSegmentResponse]] = {}
        for segment in segments:
            leg_key = (
                segment.departureDate,
                segment.origin.name,
                segment.destination.name,
            )
            legs_segments.setdefault(leg_key, []).append(segment)

        cache_key_map: dict[str, LegLookupKey] = {}
        for leg_key in legs_segments:
            cache_key = self._cache_key_for_leg_key(leg_key, telecodes)
            if cache_key:
                cache_key_map[cache_key] = leg_key
        if not cache_key_map:
            return result, resolved_legs

        values = await self._redis.mget(list(cache_key_map.keys()))
        for cache_key, raw in zip(cache_key_map.keys(), values, strict=False):
            if raw is None:
                continue
            leg_key = cache_key_map[cache_key]
            if self._is_failure_cache_value(raw):
                resolved_legs.add(leg_key)
                continue
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(payload, dict):
                continue
            resolved_legs.add(leg_key)
            for segment in legs_segments[leg_key]:
                ticket = self._ticket_from_leg_payload(payload, segment)
                if ticket is None:
                    continue
                result[self._segment_lookup_key(segment)] = ticket
        return result, resolved_legs

    def _merge_route_tickets(
        self,
        route: RouteResponse,
        ticket_map: dict[tuple[str, str, str, str], TicketSegmentData],
    ) -> RouteResponse:
        next_segs: list[RouteTrainSegmentResponse | RouteTransferSegmentResponse] = []
        statuses: list[str] = []
        for segment in route.segs:
            if not isinstance(segment, RouteTrainSegmentResponse):
                next_segs.append(segment)
                continue

            lookup_key = (
                segment.departureDate,
                segment.trainNo,
                segment.origin.name,
                segment.destination.name,
            )
            ticket = ticket_map.get(lookup_key)
            if ticket is None:
                next_segs.append(
                    segment.model_copy(
                        update={"ticketStatus": "unavailable", "seats": []}
                    )
                )
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

    def _merge_route_tickets_cache_only(
        self,
        route: RouteResponse,
        ticket_map: dict[tuple[str, str, str, str], TicketSegmentData],
    ) -> RouteResponse:
        """Like _merge_route_tickets but marks uncached segments as loading."""
        next_segs: list[RouteTrainSegmentResponse | RouteTransferSegmentResponse] = []
        statuses: list[str] = []
        for segment in route.segs:
            if not isinstance(segment, RouteTrainSegmentResponse):
                next_segs.append(segment)
                continue

            lookup_key = (
                segment.departureDate,
                segment.trainNo,
                segment.origin.name,
                segment.destination.name,
            )
            ticket = ticket_map.get(lookup_key)
            if ticket is None:
                next_segs.append(
                    segment.model_copy(
                        update={"ticketStatus": "loading", "seats": []}
                    )
                )
                statuses.append("loading")
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

    def _derive_route_status(
        self, statuses: list[str]
    ) -> Literal["ready", "partial", "unavailable", "disabled", "loading"]:
        if not statuses:
            return "disabled"
        unique_statuses = set(statuses)
        if unique_statuses == {"ready"}:
            return "ready"
        if unique_statuses == {"loading"}:
            return "loading"
        if "ready" in unique_statuses:
            return "partial"
        if "loading" in unique_statuses:
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

    @staticmethod
    def _segment_lookup_key(
        segment: CachedTrainSegment | RouteTrainSegmentResponse,
    ) -> SegmentLookupKey:
        return (
            segment.departureDate,
            segment.trainNo,
            segment.origin.name,
            segment.destination.name,
        )

    def _cache_key_for_leg_key(
        self,
        leg_key: LegLookupKey,
        telecodes: dict[str, str],
    ) -> str | None:
        run_date, from_station, to_station = leg_key
        from_code = telecodes.get(from_station)
        to_code = telecodes.get(to_station)
        if not from_code or not to_code:
            return None
        return self._build_leg_cache_key(
            run_date=run_date,
            from_station=from_station,
            to_station=to_station,
        )

    @staticmethod
    def _build_leg_cache_key(
        *,
        run_date: str,
        from_station: str,
        to_station: str,
    ) -> str:
        return (
            f"journey_search:ticket_segment:v3:{run_date}:"
            f"{from_station}:{to_station}"
        )

    @staticmethod
    def _is_failure_cache_value(raw: Any) -> bool:
        return bool(raw == "" or raw == b"")

    @staticmethod
    def _ticket_from_rows(
        rows: dict[str, Any],
        *,
        train_no: str,
        station_train_code: str,
    ) -> TicketSegmentData | None:
        row = rows.get(train_no)
        matched_by = "train_no"
        if row is None:
            row = rows.get(station_train_code)
            matched_by = "station_train_code"
        if row is None:
            return None
        seat_status, seat_prices = row
        seats = build_seat_infos(seat_status, seat_prices)
        return TicketSegmentData(
            seats=seats,
            min_price=segment_min_price(seats),
            matched_by=matched_by,
        )

    def _ticket_from_leg_payload(
        self,
        payload: dict[str, Any],
        segment: CachedTrainSegment | RouteTrainSegmentResponse,
    ) -> TicketSegmentData | None:
        entry = payload.get(segment.trainNo)
        matched_by = "train_no"
        if entry is None:
            entry = payload.get(segment.no)
            matched_by = "station_train_code"
        if not isinstance(entry, dict):
            return None
        ticket = self._decode_ticket_cache_entry(entry)
        if ticket is None:
            return None
        return TicketSegmentData(
            seats=ticket.seats,
            min_price=ticket.min_price,
            matched_by=matched_by,
        )

    def _ticket_to_price_entry(self, ticket: TicketSegmentData) -> PriceCacheEntry:
        return PriceCacheEntry(
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
    async def _store_fetched_leg_caches(
        self,
        *,
        fetched_legs: dict[LegLookupKey, dict[str, Any]],
        leg_telecodes: dict[LegLookupKey, tuple[str, str]],
    ) -> None:
        for leg_key, rows in fetched_legs.items():
            codes = leg_telecodes.get(leg_key)
            if codes is None:
                continue
            departure_date, _from_station, _to_station = leg_key
            redis_key = self._build_leg_cache_key(
                run_date=departure_date,
                from_station=_from_station,
                to_station=_to_station,
            )
            if not rows:
                try:
                    await self._redis.setex(
                        redis_key,
                        self._failure_ttl_seconds,
                        "",
                    )
                except Exception as exc:
                    logger.warning(
                        "Failed to write leg cache for %s: %s", redis_key, exc
                    )
                continue

            payload: dict[str, Any] = {}
            for train_no in self._extract_train_nos_from_rows(rows):
                ticket = self._ticket_from_rows(
                    rows,
                    train_no=train_no,
                    station_train_code=train_no,
                )
                if ticket is not None:
                    payload[train_no] = self._encode_ticket_cache_entry(ticket)
            try:
                await self._redis.setex(
                    redis_key,
                    self._cache_ttl_seconds,
                    json.dumps(payload, ensure_ascii=False),
                )
            except Exception as exc:
                logger.warning(
                    "Failed to write leg cache for %s: %s", redis_key, exc
                )

    @staticmethod
    def _encode_ticket_cache_entry(ticket: TicketSegmentData) -> dict[str, Any]:
        return {
            "seats": [
                [
                    seat.seat_type,
                    seat.status,
                    seat.price,
                    1 if seat.available else 0,
                ]
                for seat in ticket.seats
            ],
            "min_price": ticket.min_price,
        }

    @staticmethod
    def _decode_ticket_cache_entry(entry: dict[str, Any]) -> TicketSegmentData | None:
        seats_raw = entry.get("seats")
        if not isinstance(seats_raw, list):
            return None
        seats: list[SeatInfo] = []
        for item in seats_raw:
            if not isinstance(item, list | tuple) or len(item) != 4:
                return None
            seat_type, status, price, available = item
            if not isinstance(seat_type, str) or not isinstance(status, str):
                return None
            if price is not None and not isinstance(price, int | float):
                return None
            seats.append(
                SeatInfo(
                    seat_type=seat_type,
                    status=status,
                    price=float(price) if price is not None else None,
                    available=bool(available),
                )
            )
        min_price = entry.get("min_price")
        if min_price is not None and not isinstance(min_price, int | float):
            return None
        return TicketSegmentData(
            seats=seats,
            min_price=float(min_price) if min_price is not None else None,
            matched_by="",
        )

    @staticmethod
    def _extract_train_nos_from_rows(rows: dict[str, Any]) -> list[str]:
        """Return the canonical (long-form) train_no keys from a parsed leg dict.

        ``parse_query_rows`` indexes each parsed row under both ``train_no``
        and ``station_train_code``, so the dict has up to two keys pointing at
        the same tuple. We group by row identity and pick the longer key per
        group as the canonical train_no, since 12306 train_no codes are always
        longer than station_train_code labels.
        """
        by_row: dict[int, list[str]] = {}
        for key, row in rows.items():
            by_row.setdefault(id(row), []).append(key)
        train_nos: list[str] = []
        for keys in by_row.values():
            if not keys:
                continue
            train_nos.append(max(keys, key=len))
        return train_nos
