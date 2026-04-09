from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.database import BaseRepository


@dataclass(frozen=True)
class StationListFilters:
    page: int
    page_size: int
    keyword: str | None
    geo_status: str
    geo_source: str
    area_name: str | None
    sort_by: str
    sort_order: str


@dataclass(frozen=True)
class TrainListFilters:
    page: int
    page_size: int
    keyword: str | None
    is_active: str
    sort_by: str
    sort_order: str


class AdminDataRepository(BaseRepository):
    async def list_stations(
        self,
        filters: StationListFilters,
    ) -> tuple[list[dict[str, object]], int]:
        where_sql, params = _build_station_where(filters)
        order_sql = _build_station_order(filters.sort_by, filters.sort_order)
        count_sql = f"SELECT COUNT(*) AS total FROM stations s WHERE {where_sql}"
        offset = (filters.page - 1) * filters.page_size
        data_params = [*params, filters.page_size, offset]
        data_sql = f"""
            SELECT
                s.id,
                s.name,
                s.telecode,
                s.pinyin,
                s.abbr,
                s.area_name,
                s.country_name,
                s.longitude,
                s.latitude,
                s.geo_source,
                s.geo_updated_at,
                s.updated_at,
                CASE
                    WHEN s.longitude IS NOT NULL AND s.latitude IS NOT NULL THEN 'complete'
                    ELSE 'missing'
                END AS geo_status
            FROM stations s
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT ${len(params) + 1}
            OFFSET ${len(params) + 2}
        """
        async with self._pool.acquire() as conn:
            count_row = await conn.fetchrow(count_sql, *params)
            rows = await conn.fetch(data_sql, *data_params)
        total = int(count_row["total"]) if count_row and count_row["total"] is not None else 0
        return [dict(row) for row in rows], total

    async def update_station_geo(
        self,
        station_id: int,
        longitude: float | None,
        latitude: float | None,
        geo_source: str,
    ) -> dict[str, object] | None:
        sql = """
            UPDATE stations
            SET longitude = $2,
                latitude = $3,
                geo_source = $4,
                geo_updated_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
            RETURNING
                id,
                name,
                telecode,
                pinyin,
                abbr,
                area_name,
                country_name,
                longitude,
                latitude,
                geo_source,
                geo_updated_at,
                updated_at,
                CASE
                    WHEN longitude IS NOT NULL AND latitude IS NOT NULL THEN 'complete'
                    ELSE 'missing'
                END AS geo_status
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, station_id, longitude, latitude, geo_source)
        return dict(row) if row else None

    async def list_trains(
        self,
        filters: TrainListFilters,
    ) -> tuple[list[dict[str, object]], int]:
        where_sql, params = _build_train_where(filters)
        order_sql = _build_train_order(filters.sort_by, filters.sort_order)
        count_sql = f"SELECT COUNT(*) AS total FROM trains t WHERE {where_sql}"
        offset = (filters.page - 1) * filters.page_size
        data_params = [*params, filters.page_size, offset]
        data_sql = f"""
            SELECT
                t.id,
                t.train_no,
                t.station_train_code,
                t.from_station,
                t.to_station,
                t.total_num,
                t.is_active,
                t.updated_at
            FROM trains t
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT ${len(params) + 1}
            OFFSET ${len(params) + 2}
        """
        async with self._pool.acquire() as conn:
            count_row = await conn.fetchrow(count_sql, *params)
            rows = await conn.fetch(data_sql, *data_params)
        total = int(count_row["total"]) if count_row and count_row["total"] is not None else 0
        return [dict(row) for row in rows], total

    async def find_train_stops_by_train_id(
        self,
        train_id: int,
    ) -> list[dict[str, object]] | None:
        train_sql = "SELECT train_no FROM trains WHERE id = $1"
        stops_sql = """
            SELECT
                station_no,
                station_name,
                station_train_code,
                arrive_time,
                start_time,
                running_time,
                arrive_day_diff,
                arrive_day_str,
                is_start,
                start_station_name,
                end_station_name,
                train_class_name,
                service_type,
                wz_num,
                updated_at
            FROM train_stops
            WHERE train_no = $1
            ORDER BY station_no
        """
        async with self._pool.acquire() as conn:
            train_row = await conn.fetchrow(train_sql, train_id)
            if not train_row or not train_row["train_no"]:
                return None
            rows = await conn.fetch(stops_sql, train_row["train_no"])
        return [dict(row) for row in rows]


def calc_total_pages(total: int, page_size: int) -> int:
    if total <= 0:
        return 0
    return math.ceil(total / page_size)


def _build_station_where(filters: StationListFilters) -> tuple[str, list[object]]:
    clauses = ["1=1"]
    params: list[object] = []

    if filters.keyword:
        pattern = f"%{filters.keyword}%"
        params.append(pattern)
        idx = len(params)
        clauses.append(
            "("
            f"s.name ILIKE ${idx} OR "
            f"s.telecode ILIKE ${idx} OR "
            f"COALESCE(s.pinyin, '') ILIKE ${idx} OR "
            f"COALESCE(s.abbr, '') ILIKE ${idx}"
            ")"
        )

    if filters.geo_status == "missing":
        clauses.append("(s.longitude IS NULL OR s.latitude IS NULL)")
    elif filters.geo_status == "complete":
        clauses.append("(s.longitude IS NOT NULL AND s.latitude IS NOT NULL)")

    if filters.geo_source != "all":
        params.append(filters.geo_source)
        clauses.append(f"COALESCE(s.geo_source, '') = ${len(params)}")

    if filters.area_name:
        params.append(f"%{filters.area_name}%")
        clauses.append(f"COALESCE(s.area_name, '') ILIKE ${len(params)}")

    return " AND ".join(clauses), params


def _build_train_where(filters: TrainListFilters) -> tuple[str, list[object]]:
    clauses = ["1=1"]
    params: list[object] = []

    if filters.keyword:
        pattern = f"%{filters.keyword}%"
        params.append(pattern)
        idx = len(params)
        clauses.append(
            "("
            f"t.train_no ILIKE ${idx} OR "
            f"COALESCE(t.station_train_code, '') ILIKE ${idx} OR "
            f"COALESCE(t.from_station, '') ILIKE ${idx} OR "
            f"COALESCE(t.to_station, '') ILIKE ${idx}"
            ")"
        )

    if filters.is_active == "true":
        clauses.append("t.is_active = TRUE")
    elif filters.is_active == "false":
        clauses.append("t.is_active = FALSE")

    return " AND ".join(clauses), params


def _build_station_order(sort_by: str, sort_order: str) -> str:
    sort_map = {
        "id": "s.id",
        "name": "s.name",
        "geoUpdatedAt": "s.geo_updated_at",
        "updatedAt": "s.updated_at",
    }
    order = "ASC" if sort_order == "asc" else "DESC"
    column = sort_map.get(sort_by, "s.updated_at")
    nulls = "NULLS FIRST" if order == "ASC" else "NULLS LAST"
    return f"{column} {order} {nulls}, s.id ASC"


def _build_train_order(sort_by: str, sort_order: str) -> str:
    sort_map = {
        "id": "t.id",
        "trainNo": "t.train_no",
        "stationTrainCode": "t.station_train_code",
        "updatedAt": "t.updated_at",
    }
    order = "ASC" if sort_order == "asc" else "DESC"
    column = sort_map.get(sort_by, "t.updated_at")
    nulls = "NULLS FIRST" if order == "ASC" else "NULLS LAST"
    return f"{column} {order} {nulls}, t.id ASC"
