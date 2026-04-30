from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import UUID

from app.database import BaseRepository
from app.journey_search_sessions.schemas import (
    CachedRouteCandidate,
    CachedTrainSegment,
    RoutePointResponse,
    RouteStationResponse,
    RouteTransferSegmentResponse,
)


@dataclass(frozen=True)
class RoutePlanQueryFilters:
    allowed_train_types: frozenset[str] = field(default_factory=frozenset)
    excluded_train_types: frozenset[str] = field(default_factory=frozenset)
    allowed_trains: frozenset[str] = field(default_factory=frozenset)
    excluded_trains: frozenset[str] = field(default_factory=frozenset)
    departure_time_start_min: int | None = None
    departure_time_end_min: int | None = None
    arrival_deadline_abs_min: int | None = None
    min_transfer_minutes: int = 0
    max_transfer_minutes: int | None = None
    allowed_transfer_stations: frozenset[str] = field(default_factory=frozenset)
    excluded_transfer_stations: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class RoutePlanViewQuery:
    filters: RoutePlanQueryFilters
    sort_by: str
    page: int
    page_size: int
    transfer_counts: frozenset[int] = field(default_factory=frozenset)
    display_train_types: frozenset[str] = field(default_factory=frozenset)
    exclude_direct_train_codes_in_transfer_routes: bool = False


@dataclass(frozen=True)
class RoutePlanAvailableFacets:
    transfer_counts: list[int]
    train_types: list[str]


@dataclass(frozen=True)
class RoutePlanViewResult:
    candidates: list[CachedRouteCandidate]
    total: int
    facets: RoutePlanAvailableFacets


def _get_train_segments(candidate: CachedRouteCandidate) -> list[CachedTrainSegment]:
    return [
        segment
        for segment in candidate.segs
        if isinstance(segment, CachedTrainSegment)
        and not isinstance(segment, RouteTransferSegmentResponse)
    ]


def _to_date(value: str) -> date:
    return date.fromisoformat(value)


def _time_to_minutes(value: str) -> int:
    hours, minutes = value.split(":", maxsplit=1)
    return int(hours) * 60 + int(minutes)


def _get_train_type(train_code: str) -> str:
    code = train_code.strip().upper()
    prefix = ""
    for character in code:
        if not character.isalpha():
            break
        prefix += character
    return prefix


def _abs_minutes(value_date: str, value_time: str, search_date: date) -> int:
    current_date = _to_date(value_date)
    day_offset = (current_date - search_date).days
    return day_offset * 1440 + _time_to_minutes(value_time)


def _candidate_waits(candidate: CachedRouteCandidate, search_date: date) -> list[int]:
    train_segments = _get_train_segments(candidate)
    waits: list[int] = []
    for previous, current in zip(train_segments, train_segments[1:], strict=False):
        previous_arrival = _abs_minutes(
            previous.arrivalDate,
            previous.arrivalTime,
            search_date,
        )
        current_departure = _abs_minutes(
            current.departureDate,
            current.departureTime,
            search_date,
        )
        waits.append(current_departure - previous_arrival)
    return waits


def _station_row(station: RouteStationResponse) -> dict[str, Any]:
    return {
        "name": station.name,
        "code": station.code,
        "city": station.city,
        "lng": station.lng,
        "lat": station.lat,
    }


def _point_row(point: RoutePointResponse) -> dict[str, Any]:
    return {
        "lng": point.lng,
        "lat": point.lat,
    }


def _encode_jsonb(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _decode_jsonb(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


class RoutePlanRepository(BaseRepository):
    async def find_ready_plan(
        self,
        *,
        from_station: str,
        to_station: str,
        search_date: date,
        transfer_count: int,
    ) -> dict[str, Any] | None:
        sql = """
            SELECT plan_id,
                   from_station,
                   to_station,
                   search_date,
                   transfer_count,
                   status,
                   total_candidates,
                   created_at,
                   updated_at
            FROM route_plan_cache
            WHERE from_station = $1
              AND to_station = $2
              AND search_date = $3
              AND transfer_count = $4
              AND status = 1
            LIMIT 1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                sql,
                from_station,
                to_station,
                search_date,
                transfer_count,
            )
        return dict(row) if row else None

    async def get_plans_by_ids(self, plan_ids: Iterable[str]) -> list[dict[str, Any]]:
        ids = [UUID(plan_id) for plan_id in plan_ids]
        if not ids:
            return []

        sql = """
            SELECT plan_id,
                   from_station,
                   to_station,
                   search_date,
                   transfer_count,
                   status,
                   total_candidates,
                   created_at,
                   updated_at
            FROM route_plan_cache
            WHERE plan_id = ANY($1::uuid[])
              AND status = 1
            ORDER BY transfer_count, plan_id
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, ids)
        return [dict(row) for row in rows]

    async def replace_plan(
        self,
        *,
        from_station: str,
        to_station: str,
        search_date: date,
        transfer_count: int,
        candidates: list[CachedRouteCandidate],
    ) -> dict[str, Any]:
        async with self._pool.acquire() as conn, conn.transaction():
            plan = await conn.fetchrow(
                """
                INSERT INTO route_plan_cache (
                    from_station,
                    to_station,
                    search_date,
                    transfer_count,
                    status,
                    total_candidates
                )
                VALUES ($1, $2, $3, $4, 0, 0)
                ON CONFLICT (from_station, to_station, search_date, transfer_count)
                DO UPDATE SET
                    status = 0,
                    total_candidates = 0,
                    updated_at = NOW()
                RETURNING plan_id,
                          from_station,
                          to_station,
                          search_date,
                          transfer_count,
                          status,
                          total_candidates,
                          created_at,
                          updated_at
                """,
                from_station,
                to_station,
                search_date,
                transfer_count,
            )
            if plan is None:
                raise RuntimeError("failed to create route plan cache row")

            plan_id = plan["plan_id"]
            await conn.execute(
                "DELETE FROM route_plan_segment WHERE plan_id = $1",
                plan_id,
            )
            await conn.execute(
                "DELETE FROM route_plan_candidate WHERE plan_id = $1",
                plan_id,
            )

            if candidates:
                duration_ranks = self._rank_candidates(
                    candidates,
                    key=lambda candidate: (
                        candidate.transferCount,
                        candidate.durationMinutes,
                        candidate.departureDate,
                        candidate.departureTime,
                        candidate.arrivalDate,
                        candidate.arrivalTime,
                        candidate.id,
                    ),
                )
                departure_ranks = self._rank_candidates(
                    candidates,
                    key=lambda candidate: (
                        candidate.transferCount,
                        _abs_minutes(
                            candidate.departureDate,
                            candidate.departureTime,
                            search_date,
                        ),
                        candidate.durationMinutes,
                        _abs_minutes(
                            candidate.arrivalDate,
                            candidate.arrivalTime,
                            search_date,
                        ),
                        candidate.id,
                    ),
                )
                candidate_rows = [
                    self._candidate_row(
                        plan_id,
                        candidate,
                        search_date,
                        duration_ranks[candidate.id],
                        departure_ranks[candidate.id],
                    )
                    for candidate in candidates
                ]
                await conn.executemany(
                    """
                    INSERT INTO route_plan_candidate (
                        plan_id,
                        route_id,
                        transfer_count,
                        is_direct,
                        origin_station,
                        destination_station,
                        origin_station_snapshot,
                        destination_station_snapshot,
                        path_points,
                        train_no_label,
                        route_type,
                        departure_date,
                        departure_time,
                        arrival_date,
                        arrival_time,
                        departure_abs_min,
                        arrival_abs_min,
                        duration_minutes,
                        train_codes,
                        train_nos,
                        train_types,
                        transfer_stations,
                        min_wait_minutes,
                        max_wait_minutes,
                        total_wait_minutes,
                        duration_rank,
                        departure_rank
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb,
                        $9::jsonb, $10, $11, $12, $13, $14, $15, $16,
                        $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27
                    )
                    """,
                    candidate_rows,
                )

                segment_rows = [
                    self._segment_row(plan_id, candidate, segment, search_date, index)
                    for candidate in candidates
                    for index, segment in enumerate(_get_train_segments(candidate))
                ]
                await conn.executemany(
                    """
                    INSERT INTO route_plan_segment (
                        plan_id,
                        route_id,
                        segment_index,
                        train_no,
                        train_code,
                        train_type,
                        from_station,
                        to_station,
                        origin_station_snapshot,
                        destination_station_snapshot,
                        departure_date,
                        departure_time,
                        arrival_date,
                        arrival_time,
                        departure_abs_min,
                        arrival_abs_min,
                        duration_minutes,
                        stops_count
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8,
                        $9::jsonb, $10::jsonb, $11, $12, $13, $14,
                        $15, $16, $17, $18
                    )
                    """,
                    segment_rows,
                )

            updated = await conn.fetchrow(
                """
                UPDATE route_plan_cache
                SET status = 1,
                    total_candidates = $2,
                    updated_at = NOW()
                WHERE plan_id = $1
                RETURNING plan_id,
                          from_station,
                          to_station,
                          search_date,
                          transfer_count,
                          status,
                          total_candidates,
                          created_at,
                          updated_at
                """,
                plan_id,
                len(candidates),
            )
        if updated is None:
            raise RuntimeError("failed to mark route plan cache as ready")
        return dict(updated)

    async def count_candidates(
        self,
        plan_ids: Iterable[str],
        filters: RoutePlanQueryFilters,
    ) -> int:
        ids = [UUID(plan_id) for plan_id in plan_ids]
        if not ids:
            return 0

        where_sql, params = self._build_base_where(ids, filters)
        sql = f"""
            SELECT COUNT(*) AS total
            FROM route_plan_candidate
            WHERE {where_sql}
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, *params)
        return int(row["total"]) if row else 0

    async def query_view(
        self,
        plan_ids: Iterable[str],
        query: RoutePlanViewQuery,
    ) -> RoutePlanViewResult:
        ids = [UUID(plan_id) for plan_id in plan_ids]
        if not ids:
            return RoutePlanViewResult(
                candidates=[],
                total=0,
                facets=RoutePlanAvailableFacets(transfer_counts=[], train_types=[]),
            )

        facets = await self._available_facets(ids, query.filters)
        where_sql, params = self._build_base_where(ids, query.filters)
        direct_codes = await self._direct_train_codes(ids, query.filters)
        where_sql, params = self._apply_view_where(
            where_sql,
            params,
            query,
            direct_codes,
        )

        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM route_plan_candidate
            WHERE {where_sql}
        """
        order_sql = self._order_sql(query.sort_by)
        offset = (query.page - 1) * query.page_size
        count_params = list(params)
        limit_ref = self._add_param(params, query.page_size)
        offset_ref = self._add_param(params, offset)
        candidate_sql = f"""
            SELECT plan_id,
                   route_id,
                   transfer_count,
                   is_direct,
                   origin_station_snapshot,
                   destination_station_snapshot,
                   path_points,
                   train_no_label,
                   route_type,
                   departure_date,
                   departure_time,
                   arrival_date,
                   arrival_time,
                   duration_minutes,
                   train_codes,
                   train_nos,
                   train_types
            FROM route_plan_candidate
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT {limit_ref}
            OFFSET {offset_ref}
        """
        async with self._pool.acquire() as conn:
            count_row = await conn.fetchrow(count_sql, *count_params)
            candidate_rows = await conn.fetch(candidate_sql, *params)

        total = int(count_row["total"]) if count_row else 0
        if not candidate_rows:
            return RoutePlanViewResult(candidates=[], total=total, facets=facets)

        segment_rows = await self._fetch_segments_for_candidates(candidate_rows)
        segments_by_route: dict[tuple[str, str], list[CachedTrainSegment]] = {}
        for row in segment_rows:
            key = (str(row["plan_id"]), str(row["route_id"]))
            segments_by_route.setdefault(key, []).append(self._segment_from_row(dict(row)))

        candidates = [
            self._candidate_from_row(
                dict(row),
                segments_by_route.get((str(row["plan_id"]), str(row["route_id"])), []),
            )
            for row in candidate_rows
        ]
        return RoutePlanViewResult(candidates=candidates, total=total, facets=facets)

    async def delete_plans(self, plan_ids: Iterable[str]) -> int:
        ids = [UUID(plan_id) for plan_id in plan_ids]
        if not ids:
            return 0

        sql = "DELETE FROM route_plan_cache WHERE plan_id = ANY($1::uuid[])"
        async with self._pool.acquire() as conn:
            result = await conn.execute(sql, ids)
        return int(result.rsplit(" ", maxsplit=1)[-1])

    def _candidate_row(
        self,
        plan_id: UUID,
        candidate: CachedRouteCandidate,
        search_date: date,
        duration_rank: int,
        departure_rank: int,
    ) -> tuple[object, ...]:
        train_segments = _get_train_segments(candidate)
        transfer_stations = [segment.destination.name for segment in train_segments[:-1]]
        waits = _candidate_waits(candidate, search_date)
        departure_abs_min = _abs_minutes(
            candidate.departureDate,
            candidate.departureTime,
            search_date,
        )
        arrival_abs_min = _abs_minutes(
            candidate.arrivalDate,
            candidate.arrivalTime,
            search_date,
        )
        return (
            plan_id,
            candidate.id,
            candidate.transferCount,
            candidate.isDirect,
            candidate.origin.name,
            candidate.destination.name,
            _encode_jsonb(_station_row(candidate.origin)),
            _encode_jsonb(_station_row(candidate.destination)),
            _encode_jsonb([_point_row(point) for point in candidate.pathPoints]),
            candidate.trainNo,
            candidate.type,
            _to_date(candidate.departureDate),
            candidate.departureTime,
            _to_date(candidate.arrivalDate),
            candidate.arrivalTime,
            departure_abs_min,
            arrival_abs_min,
            candidate.durationMinutes,
            candidate.trainCodes,
            [segment.trainNo.strip().upper() for segment in train_segments],
            candidate.trainTypes,
            transfer_stations,
            min(waits) if waits else None,
            max(waits) if waits else None,
            sum(waits) if waits else 0,
            duration_rank,
            departure_rank,
        )

    def _segment_row(
        self,
        plan_id: UUID,
        candidate: CachedRouteCandidate,
        segment: CachedTrainSegment,
        search_date: date,
        index: int,
    ) -> tuple[object, ...]:
        departure_abs_min = _abs_minutes(
            segment.departureDate,
            segment.departureTime,
            search_date,
        )
        arrival_abs_min = _abs_minutes(
            segment.arrivalDate,
            segment.arrivalTime,
            search_date,
        )
        return (
            plan_id,
            candidate.id,
            index,
            segment.trainNo,
            segment.no,
            _get_train_type(segment.no),
            segment.origin.name,
            segment.destination.name,
            _encode_jsonb(_station_row(segment.origin)),
            _encode_jsonb(_station_row(segment.destination)),
            _to_date(segment.departureDate),
            segment.departureTime,
            _to_date(segment.arrivalDate),
            segment.arrivalTime,
            departure_abs_min,
            arrival_abs_min,
            arrival_abs_min - departure_abs_min,
            segment.stopsCount,
        )

    def _candidate_from_row(
        self,
        row: dict[str, Any],
        segments: list[CachedTrainSegment],
    ) -> CachedRouteCandidate:
        segs: list[CachedTrainSegment | RouteTransferSegmentResponse] = []
        for index, segment in enumerate(segments):
            segs.append(segment)
            if index < len(segments) - 1:
                next_segment = segments[index + 1]
                segs.append(
                    RouteTransferSegmentResponse(
                        transfer=f"{segment.destination.name} 换乘 {next_segment.no}"
                    )
                )

        return CachedRouteCandidate(
            id=str(row["route_id"]),
            trainNo=str(row["train_no_label"]),
            type=str(row["route_type"]),
            origin=self._station_from_snapshot(_decode_jsonb(row["origin_station_snapshot"])),
            destination=self._station_from_snapshot(
                _decode_jsonb(row["destination_station_snapshot"])
            ),
            departureDate=row["departure_date"].isoformat(),
            departureTime=str(row["departure_time"]),
            arrivalDate=row["arrival_date"].isoformat(),
            arrivalTime=str(row["arrival_time"]),
            durationMinutes=int(row["duration_minutes"]),
            segs=segs,
            pathPoints=[
                RoutePointResponse(lng=float(point["lng"]), lat=float(point["lat"]))
                for point in _decode_jsonb(row["path_points"])
            ],
            isDirect=bool(row["is_direct"]),
            transferCount=int(row["transfer_count"]),
            trainTypes=[str(item) for item in row["train_types"]],
            trainCodes=[str(item) for item in row["train_codes"]],
        )

    def _segment_from_row(self, row: dict[str, Any]) -> CachedTrainSegment:
        return CachedTrainSegment(
            trainNo=str(row["train_no"]),
            no=str(row["train_code"]),
            origin=self._station_from_snapshot(_decode_jsonb(row["origin_station_snapshot"])),
            destination=self._station_from_snapshot(
                _decode_jsonb(row["destination_station_snapshot"])
            ),
            departureDate=row["departure_date"].isoformat(),
            departureTime=str(row["departure_time"]),
            arrivalDate=row["arrival_date"].isoformat(),
            arrivalTime=str(row["arrival_time"]),
            stopsCount=(
                int(row["stops_count"])
                if row.get("stops_count") is not None
                else None
            ),
        )

    def _station_from_snapshot(self, payload: dict[str, Any]) -> RouteStationResponse:
        return RouteStationResponse(
            name=str(payload["name"]),
            code=str(payload.get("code", "")),
            city=str(payload.get("city", "")),
            lng=float(payload["lng"]),
            lat=float(payload["lat"]),
        )

    async def _available_facets(
        self,
        ids: list[UUID],
        filters: RoutePlanQueryFilters,
    ) -> RoutePlanAvailableFacets:
        where_sql, params = self._build_base_where(ids, filters)
        transfer_sql = f"""
            SELECT DISTINCT transfer_count
            FROM route_plan_candidate
            WHERE {where_sql}
            ORDER BY transfer_count
        """
        train_type_sql = f"""
            SELECT DISTINCT unnest(train_types) AS train_type
            FROM route_plan_candidate
            WHERE {where_sql}
            ORDER BY train_type
        """
        async with self._pool.acquire() as conn:
            transfer_rows = await conn.fetch(transfer_sql, *params)
            train_type_rows = await conn.fetch(train_type_sql, *params)
        return RoutePlanAvailableFacets(
            transfer_counts=[int(row["transfer_count"]) for row in transfer_rows],
            train_types=[str(row["train_type"]) for row in train_type_rows],
        )

    async def _direct_train_codes(
        self,
        ids: list[UUID],
        filters: RoutePlanQueryFilters,
    ) -> list[str]:
        where_sql, params = self._build_base_where(ids, filters)
        sql = f"""
            SELECT DISTINCT unnest(train_codes) AS train_code
            FROM route_plan_candidate
            WHERE {where_sql}
              AND is_direct = TRUE
            ORDER BY train_code
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
        return [str(row["train_code"]) for row in rows]

    async def _fetch_segments_for_candidates(self, candidate_rows: list[Any]) -> list[Any]:
        plan_ids = [row["plan_id"] for row in candidate_rows]
        route_ids = [str(row["route_id"]) for row in candidate_rows]
        sql = """
            WITH requested(plan_id, route_id) AS (
                SELECT *
                FROM unnest($1::uuid[], $2::text[]) AS item(plan_id, route_id)
            )
            SELECT segment.plan_id,
                   segment.route_id,
                   segment.segment_index,
                   segment.train_no,
                   segment.train_code,
                   segment.origin_station_snapshot,
                   segment.destination_station_snapshot,
                   segment.departure_date,
                   segment.departure_time,
                   segment.arrival_date,
                   segment.arrival_time,
                   segment.stops_count
            FROM route_plan_segment segment
            JOIN requested
              ON requested.plan_id = segment.plan_id
             AND requested.route_id = segment.route_id
            ORDER BY segment.plan_id, segment.route_id, segment.segment_index
        """
        async with self._pool.acquire() as conn:
            return await conn.fetch(sql, plan_ids, route_ids)

    def _build_base_where(
        self,
        ids: list[UUID],
        filters: RoutePlanQueryFilters,
    ) -> tuple[str, list[object]]:
        params: list[object] = [ids]
        conditions = ["plan_id = ANY($1::uuid[])"]

        if filters.allowed_train_types:
            ref = self._add_param(params, sorted(filters.allowed_train_types), "::text[]")
            conditions.append(f"train_types <@ {ref}")
        if filters.excluded_train_types:
            ref = self._add_param(params, sorted(filters.excluded_train_types), "::text[]")
            conditions.append(f"NOT (train_types && {ref})")
        if filters.allowed_trains:
            ref = self._add_param(params, sorted(filters.allowed_trains), "::text[]")
            conditions.append(f"(train_codes && {ref} OR train_nos && {ref})")
        if filters.excluded_trains:
            ref = self._add_param(params, sorted(filters.excluded_trains), "::text[]")
            conditions.append(f"NOT (train_codes && {ref} OR train_nos && {ref})")
        if (
            filters.departure_time_start_min is not None
            and filters.departure_time_end_min is not None
        ):
            start_ref = self._add_param(params, filters.departure_time_start_min)
            end_ref = self._add_param(params, filters.departure_time_end_min)
            if filters.departure_time_start_min > filters.departure_time_end_min:
                conditions.append(
                    f"(departure_abs_min % 1440 >= {start_ref} "
                    f"OR departure_abs_min % 1440 <= {end_ref})"
                )
            else:
                conditions.append(
                    f"departure_abs_min % 1440 BETWEEN {start_ref} AND {end_ref}"
                )
        elif filters.departure_time_start_min is not None:
            ref = self._add_param(params, filters.departure_time_start_min)
            conditions.append(f"departure_abs_min % 1440 >= {ref}")
        elif filters.departure_time_end_min is not None:
            ref = self._add_param(params, filters.departure_time_end_min)
            conditions.append(f"departure_abs_min % 1440 <= {ref}")
        if filters.arrival_deadline_abs_min is not None:
            ref = self._add_param(params, filters.arrival_deadline_abs_min)
            if filters.arrival_deadline_abs_min >= 1440:
                conditions.append(f"arrival_abs_min <= {ref}")
            else:
                conditions.append(f"arrival_abs_min % 1440 <= {ref}")
        if filters.min_transfer_minutes > 0:
            ref = self._add_param(params, filters.min_transfer_minutes)
            conditions.append("(transfer_count = 0 OR min_wait_minutes >= " + ref + ")")
        if filters.max_transfer_minutes is not None:
            ref = self._add_param(params, filters.max_transfer_minutes)
            conditions.append("(transfer_count = 0 OR max_wait_minutes <= " + ref + ")")
        if filters.allowed_transfer_stations:
            ref = self._add_param(
                params,
                sorted(filters.allowed_transfer_stations),
                "::text[]",
            )
            conditions.append(f"(transfer_count = 0 OR transfer_stations && {ref})")
        if filters.excluded_transfer_stations:
            ref = self._add_param(
                params,
                sorted(filters.excluded_transfer_stations),
                "::text[]",
            )
            conditions.append(f"NOT (transfer_stations && {ref})")

        return " AND ".join(conditions), params

    def _apply_view_where(
        self,
        where_sql: str,
        params: list[object],
        query: RoutePlanViewQuery,
        direct_codes: list[str],
    ) -> tuple[str, list[object]]:
        conditions = [where_sql]
        if query.transfer_counts:
            ref = self._add_param(params, sorted(query.transfer_counts), "::smallint[]")
            conditions.append(f"transfer_count = ANY({ref})")
        if query.exclude_direct_train_codes_in_transfer_routes and direct_codes:
            ref = self._add_param(params, direct_codes, "::text[]")
            conditions.append(f"(is_direct = TRUE OR NOT (train_codes && {ref}))")
        if query.display_train_types:
            ref = self._add_param(params, sorted(query.display_train_types), "::text[]")
            conditions.append(f"train_types <@ {ref}")
        return " AND ".join(f"({condition})" for condition in conditions), params

    def _order_sql(self, sort_by: str) -> str:
        if sort_by == "departure":
            return (
                "transfer_count ASC, departure_rank ASC, duration_rank ASC, route_id ASC"
            )
        return (
            "transfer_count ASC, duration_rank ASC, departure_rank ASC, route_id ASC"
        )

    def _rank_candidates(
        self,
        candidates: list[CachedRouteCandidate],
        key: Callable[[CachedRouteCandidate], tuple[Any, ...]],
    ) -> dict[str, int]:
        return {
            candidate.id: index
            for index, candidate in enumerate(sorted(candidates, key=key), start=1)
        }

    def _add_param(
        self,
        params: list[object],
        value: object,
        cast: str = "",
    ) -> str:
        params.append(value)
        return f"${len(params)}{cast}"
