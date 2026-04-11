from __future__ import annotations

import itertools
from datetime import date as date_type
from typing import Any

import asyncpg

from app.database import BaseRepository
from app.models import SeatInfo, SeatLookupKey, StopEvent, Timetable
from app.planner.time_utils import advance_past, parse_hhmm


class StationRepository(BaseRepository):
    async def find_all(self) -> list[dict[str, object]]:
        sql = """
            SELECT id, name, telecode, pinyin, abbr,
                   area_code, area_name, country_code, country_name,
                   longitude, latitude, geo_source, geo_updated_at
            FROM stations
            ORDER BY id
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [dict(row) for row in rows]

    async def upsert_stations(self, stations: list[dict[str, str]]) -> int:
        count = 0
        async with self._pool.acquire() as conn:
            for station in stations:
                await conn.execute(
                    """
                    INSERT INTO stations (
                        telecode,
                        name,
                        pinyin,
                        abbr,
                        area_code,
                        area_name,
                        country_code,
                        country_name
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (telecode) DO UPDATE
                    SET name = EXCLUDED.name,
                        pinyin = EXCLUDED.pinyin,
                        abbr = EXCLUDED.abbr,
                        area_code = EXCLUDED.area_code,
                        area_name = EXCLUDED.area_name,
                        country_code = EXCLUDED.country_code,
                        country_name = EXCLUDED.country_name,
                        updated_at = NOW()
                    """,
                    station.get("telecode", ""),
                    station.get("name", ""),
                    station.get("pinyin", ""),
                    station.get("abbr", ""),
                    station.get("area_code", ""),
                    station.get("area_name", ""),
                    station.get("country_code", "cn"),
                    station.get("country_name", "中国"),
                )
                count += 1
        return count

    async def find_missing_geo(self) -> list[dict[str, object]]:
        sql = """
            SELECT id, name, area_name
            FROM stations
            WHERE longitude IS NULL OR latitude IS NULL
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [dict(row) for row in rows]

    async def find_geo_enrichment_candidates(self) -> list[dict[str, object]]:
        sql = """
            SELECT id, name, area_name, longitude, latitude
            FROM stations
            WHERE longitude IS NULL OR latitude IS NULL
            ORDER BY id
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [dict(row) for row in rows]

    async def update_geo(
        self,
        station_id: int,
        longitude: float,
        latitude: float,
        geo_source: str,
    ) -> None:
        sql = """
            UPDATE stations
            SET longitude = $2,
                latitude = $3,
                geo_source = $4,
                geo_updated_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, station_id, longitude, latitude, geo_source)

    async def find_by_names(self, names: list[str]) -> list[dict[str, object]]:
        cleaned = [name.strip() for name in names if name.strip()]
        if not cleaned:
            return []

        sql = """
            SELECT id, name, telecode, pinyin, abbr,
                   area_code, area_name, country_code, country_name,
                   longitude, latitude, geo_source, geo_updated_at
            FROM stations
            WHERE name = ANY($1)
            ORDER BY id
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, cleaned)
        return [dict(row) for row in rows]

    async def get_geo_by_names(
        self,
        names: list[str],
    ) -> dict[str, tuple[float, float]]:
        cleaned = sorted({name.strip() for name in names if name.strip()})
        if not cleaned:
            return {}

        sql = """
            SELECT DISTINCT ON (name)
                name,
                longitude,
                latitude
            FROM stations
            WHERE name = ANY($1)
              AND longitude IS NOT NULL
              AND latitude IS NOT NULL
            ORDER BY name, geo_updated_at DESC NULLS LAST, id DESC
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, cleaned)

        return {
            str(row["name"]): (float(row["longitude"]), float(row["latitude"]))
            for row in rows
        }

    async def suggest_by_keyword(
        self,
        keyword: str,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        kw = keyword.strip()
        if not kw:
            return []

        sql = """
            SELECT name, telecode, pinyin, abbr
            FROM stations
            WHERE name LIKE $1
               OR pinyin LIKE $1
               OR abbr LIKE $1
            ORDER BY
                CASE
                    WHEN name = $2 THEN 0
                    WHEN name LIKE $2 || '%' THEN 1
                    WHEN abbr = $2 THEN 2
                    ELSE 3
                END,
                name
            LIMIT $3
        """
        pattern = f"%{kw}%"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, pattern, kw, limit)

        return [
            {
                "name": str(row["name"]),
                "telecode": str(row["telecode"] or ""),
                "pinyin": str(row["pinyin"] or ""),
                "abbr": str(row["abbr"] or ""),
            }
            for row in rows
        ]

    async def find_all_for_cache(self) -> list[dict[str, str]]:
        """获取所有车站的简化信息，用于前端缓存"""
        sql = """
            SELECT name, telecode, pinyin, abbr
            FROM stations
            ORDER BY name
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)

        return [
            {
                "name": str(row["name"]),
                "telecode": str(row["telecode"] or ""),
                "pinyin": str(row["pinyin"] or ""),
                "abbr": str(row["abbr"] or ""),
            }
            for row in rows
        ]

    async def get_telecodes_by_names(self, names: set[str]) -> dict[str, str]:
        cleaned = sorted({name.strip() for name in names if name.strip()})
        if not cleaned:
            return {}

        sql = """
            SELECT name, telecode
            FROM stations
            WHERE name = ANY($1)
              AND telecode IS NOT NULL
              AND telecode <> ''
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, cleaned)

        return {str(row["name"]): str(row["telecode"]) for row in rows}


class TrainRepository(BaseRepository):
    async def get_stops_by_train_code(
        self,
        train_code: str,
        from_station: str,
        to_station: str,
        full_route: bool = False,
    ) -> list[dict[str, object]]:
        train_no = await self._resolve_train_no(train_code, from_station, to_station)
        if not train_no:
            return []

        rows = await self._fetch_stop_rows(train_no)
        if not rows:
            return []

        if full_route:
            return rows

        return _slice_stops(rows, from_station, to_station) or rows

    async def _resolve_train_no(
        self,
        train_code: str,
        from_station: str,
        to_station: str,
    ) -> str | None:
        sql = """
            SELECT ts.train_no
            FROM train_stops ts
            GROUP BY ts.train_no
            HAVING (
                BOOL_OR(UPPER(ts.train_no) = UPPER($1))
                OR BOOL_OR(UPPER(ts.station_train_code) = UPPER($1))
            )
              AND BOOL_OR(ts.station_name = $2)
              AND BOOL_OR(ts.station_name = $3)
            ORDER BY
                CASE WHEN BOOL_OR(UPPER(ts.train_no) = UPPER($1)) THEN 0 ELSE 1 END,
                MIN(ts.station_no)
            LIMIT 1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, train_code, from_station, to_station)

        if not row or not row["train_no"]:
            return None
        return str(row["train_no"])

    async def _fetch_stop_rows(self, train_no: str) -> list[dict[str, object]]:
        sql = """
            SELECT
                ts.station_name,
                ts.station_no,
                ts.arrive_time,
                ts.start_time,
                ts.arrive_day_diff
            FROM train_stops ts
            WHERE UPPER(ts.train_no) = UPPER($1)
            ORDER BY ts.station_no
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, train_no)

        return [
            {
                "station_name": str(row["station_name"] or ""),
                "stop_number": int(row["station_no"]) if row["station_no"] else 0,
                "arrival_time": str(row["arrive_time"]) if row["arrive_time"] else None,
                "departure_time": str(row["start_time"]) if row["start_time"] else None,
                "arrive_day_diff": int(row["arrive_day_diff"]) if row["arrive_day_diff"] else 0,
            }
            for row in rows
        ]


class RailwayTaskRepository(BaseRepository):
    async def upsert_train_rows(self, rows: list[dict[str, Any]]) -> int:
        async with self._pool.acquire() as conn:
            return await self._upsert_train_rows(conn, rows)

    async def upsert_stop_rows(self, rows: list[dict[str, Any]]) -> int:
        async with self._pool.acquire() as conn:
            return await self._upsert_stop_rows(conn, rows)

    async def upsert_train_and_stop_rows(
        self,
        train_rows: list[dict[str, Any]],
        stop_rows: list[dict[str, Any]],
    ) -> tuple[int, int]:
        async with self._pool.acquire() as conn, conn.transaction():
            train_count = await self._upsert_train_rows(conn, train_rows)
            stop_count = await self._upsert_stop_rows(conn, stop_rows)
        return train_count, stop_count

    async def upsert_train_and_run_rows(
        self,
        train_rows: list[dict[str, Any]],
        run_rows: list[dict[str, Any]],
    ) -> tuple[int, int]:
        async with self._pool.acquire() as conn, conn.transaction():
            train_count = await self._upsert_train_rows(conn, train_rows)
            run_count = await self._upsert_run_rows(conn, run_rows)
        return train_count, run_count

    async def list_all_train_nos(self) -> list[str]:
        sql = """
            SELECT DISTINCT train_no
            FROM trains
            WHERE train_no IS NOT NULL
              AND train_no <> ''
            ORDER BY train_no
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [str(row["train_no"]) for row in rows if row["train_no"]]

    async def find_train_nos_by_keyword(self, keyword: str) -> list[str]:
        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            return []

        sql = """
            SELECT DISTINCT train_no
            FROM trains
            WHERE UPPER(train_no) = UPPER($1)
               OR UPPER(station_train_code) = UPPER($1)
            ORDER BY train_no
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, cleaned_keyword)
        return [str(row["train_no"]) for row in rows if row["train_no"]]

    async def _upsert_train_rows(
        self,
        conn: asyncpg.Connection,
        rows: list[dict[str, Any]],
    ) -> int:
        values = await _prepare_train_values(conn, rows)
        if not values:
            return 0

        await conn.executemany(
            """
            INSERT INTO trains (
              train_no, station_train_code, from_station_id, from_station,
              to_station_id, to_station, total_num, is_active
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
            ON CONFLICT (train_no) DO UPDATE SET
              station_train_code = COALESCE(
                  EXCLUDED.station_train_code,
                  trains.station_train_code
              ),
              from_station_id = COALESCE(EXCLUDED.from_station_id, trains.from_station_id),
              from_station = COALESCE(EXCLUDED.from_station, trains.from_station),
              to_station_id = COALESCE(EXCLUDED.to_station_id, trains.to_station_id),
              to_station = COALESCE(EXCLUDED.to_station, trains.to_station),
              total_num = COALESCE(EXCLUDED.total_num, trains.total_num),
              is_active = TRUE,
              updated_at = NOW()
            """,
            values,
        )
        return len(values)

    async def _upsert_stop_rows(
        self,
        conn: asyncpg.Connection,
        rows: list[dict[str, Any]],
    ) -> int:
        values = [
            (
                str(item.get("train_no") or "").strip(),
                _to_int(item.get("station_no")),
                _to_text(item.get("station_name")),
                _to_text(item.get("station_train_code")),
                _to_text(item.get("arrive_time")),
                _to_text(item.get("start_time")),
                _to_text(item.get("running_time")),
                _to_int(item.get("arrive_day_diff")),
                _to_text(item.get("arrive_day_str")),
                _to_text(item.get("is_start")),
                _to_text(item.get("start_station_name")),
                _to_text(item.get("end_station_name")),
                _to_text(item.get("train_class_name")),
                _to_text(item.get("service_type")),
                _to_text(item.get("wz_num")),
            )
            for item in rows
            if str(item.get("train_no") or "").strip()
            and (_to_int(item.get("station_no")) or 0) > 0
        ]
        if not values:
            return 0

        await conn.executemany(
            """
            INSERT INTO train_stops (
              train_no, station_no, station_name, station_train_code, arrive_time, start_time,
              running_time, arrive_day_diff, arrive_day_str, is_start, start_station_name,
              end_station_name, train_class_name, service_type, wz_num
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (train_no, station_no) DO UPDATE SET
              station_name = EXCLUDED.station_name,
              station_train_code = EXCLUDED.station_train_code,
              arrive_time = EXCLUDED.arrive_time,
              start_time = EXCLUDED.start_time,
              running_time = EXCLUDED.running_time,
              arrive_day_diff = EXCLUDED.arrive_day_diff,
              arrive_day_str = EXCLUDED.arrive_day_str,
              is_start = EXCLUDED.is_start,
              start_station_name = EXCLUDED.start_station_name,
              end_station_name = EXCLUDED.end_station_name,
              train_class_name = EXCLUDED.train_class_name,
              service_type = EXCLUDED.service_type,
              wz_num = EXCLUDED.wz_num,
              updated_at = NOW()
            """,
            values,
        )
        return len(values)

    async def _upsert_run_rows(
        self,
        conn: asyncpg.Connection,
        rows: list[dict[str, Any]],
    ) -> int:
        train_nos = sorted(
            {
                str(item.get("train_no") or "").strip()
                for item in rows
                if str(item.get("train_no") or "").strip()
            }
        )
        if not train_nos:
            return 0

        map_rows = await conn.fetch(
            "SELECT train_no, id FROM trains WHERE train_no = ANY($1)",
            train_nos,
        )
        train_id_map = {str(row["train_no"]): int(row["id"]) for row in map_rows}

        dedup: dict[tuple[int, date_type], tuple[int, date_type, str]] = {}
        for item in rows:
            train_no = str(item.get("train_no") or "").strip()
            train_id = train_id_map.get(train_no)
            run_date = _to_date(item.get("run_date") or item.get("date"))
            status = _to_text(item.get("status")) or "running"
            if train_id is None or run_date is None:
                continue
            dedup[(train_id, run_date)] = (train_id, run_date, status)

        values = list(dedup.values())
        if not values:
            return 0

        await conn.executemany(
            """
            INSERT INTO train_runs (train_id, run_date, status, source_updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (train_id, run_date) DO UPDATE SET
              status = EXCLUDED.status,
              source_updated_at = EXCLUDED.source_updated_at,
              updated_at = NOW()
            """,
            values,
        )
        return len(values)


MINUTES_PER_DAY = 1440


class TimetableRepository(BaseRepository):
    async def load_timetable(self, run_date: str, filter_running_only: bool) -> Timetable:
        if filter_running_only:
            sql = """
                SELECT
                    ts.train_no,
                    ts.station_no,
                    COALESCE(ts.station_name, '') AS station_name,
                    COALESCE(ts.station_train_code, '') AS station_train_code,
                    ts.arrive_time,
                    ts.start_time,
                    COALESCE(ts.arrive_day_diff, 0) AS arrive_day_diff
                FROM train_stops ts
                JOIN trains t ON t.train_no = ts.train_no
                JOIN train_runs tr
                    ON tr.train_id = t.id
                   AND tr.run_date = $1
                   AND tr.status = 'running'
                ORDER BY ts.train_no, ts.station_no
            """
            params: tuple[str, ...] = (run_date,)
        else:
            sql = """
                SELECT
                    ts.train_no,
                    ts.station_no,
                    COALESCE(ts.station_name, '') AS station_name,
                    COALESCE(ts.station_train_code, '') AS station_train_code,
                    ts.arrive_time,
                    ts.start_time,
                    COALESCE(ts.arrive_day_diff, 0) AS arrive_day_diff
                FROM train_stops ts
                ORDER BY ts.train_no, ts.station_no
            """
            params = ()

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        timetable: Timetable = {}
        grouped_rows = itertools.groupby(
            rows,
            key=lambda row: str(row["train_no"] or "").strip(),
        )
        for train_no, group in grouped_rows:
            if not train_no:
                continue
            events = _parse_stop_rows(train_no, list(group))
            if len(events) >= 2:
                timetable[train_no] = events

        return timetable


AVAILABILITY_STATUS_MAP = {
    "available": "有",
    "waitlist": "候补",
    "sold_out": "无",
}


class SeatRepository(BaseRepository):
    async def load_segment_seats(
        self,
        run_date: str,
        segments: set[SeatLookupKey],
    ) -> dict[SeatLookupKey, list[SeatInfo]]:
        if not segments:
            return {}

        placeholders = ", ".join(
            f"(${index * 3 + 1}, ${index * 3 + 2}, ${index * 3 + 3})"
            for index in range(len(segments))
        )
        params: list[object] = []
        for train_no, from_station, to_station in sorted(segments):
            params.extend([train_no, from_station, to_station])
        params.append(run_date)

        sql = f"""
            WITH requested(train_no, from_station, to_station) AS (
                VALUES {placeholders}
            )
            SELECT DISTINCT ON (
                requested.train_no,
                requested.from_station,
                requested.to_station,
                availability_snapshots.seat_type
            )
                requested.train_no,
                requested.from_station,
                requested.to_station,
                availability_snapshots.seat_type,
                availability_snapshots.availability_status,
                availability_snapshots.available_count
            FROM requested
            JOIN trains
                ON trains.train_no = requested.train_no
            JOIN stations from_st
                ON from_st.name = requested.from_station
            JOIN stations to_st
                ON to_st.name = requested.to_station
            JOIN availability_snapshots
                ON availability_snapshots.train_id = trains.id
               AND availability_snapshots.run_date = ${len(segments) * 3 + 1}
               AND availability_snapshots.from_station_id = from_st.id
               AND availability_snapshots.to_station_id = to_st.id
            ORDER BY
                requested.train_no,
                requested.from_station,
                requested.to_station,
                availability_snapshots.seat_type,
                availability_snapshots.snapshot_at DESC
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        result: dict[SeatLookupKey, list[SeatInfo]] = {}
        for row in rows:
            key: SeatLookupKey = (
                str(row["train_no"]),
                str(row["from_station"]),
                str(row["to_station"]),
            )
            seat = _make_seat_info(
                seat_type=str(row["seat_type"]),
                status=str(row["availability_status"]),
                available_count=(
                    int(row["available_count"])
                    if row["available_count"] is not None
                    else None
                ),
            )
            result.setdefault(key, []).append(seat)

        return result


def _slice_stops(
    stops: list[dict[str, object]],
    from_station: str,
    to_station: str,
) -> list[dict[str, object]]:
    names = [str(stop["station_name"]).strip() for stop in stops]
    try:
        start_index = names.index(from_station.strip())
        end_index = names.index(to_station.strip())
    except ValueError:
        return []

    if start_index <= end_index:
        return stops[start_index : end_index + 1]
    return list(reversed(stops[end_index : start_index + 1]))


def dedupe_train_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in rows:
        train_no = str(row.get("train_no") or "").strip()
        if not train_no or train_no in seen:
            continue
        seen.add(train_no)
        unique_rows.append(row)
    return unique_rows


async def _prepare_train_values(
    conn: asyncpg.Connection,
    rows: list[dict[str, Any]],
) -> list[tuple[str, str | None, int | None, str | None, int | None, str | None, int | None]]:
    unique_rows = dedupe_train_rows(rows)
    station_names = sorted(
        {
            str(name).strip()
            for row in unique_rows
            for name in (row.get("from_station"), row.get("to_station"))
            if str(name or "").strip()
        }
    )

    station_map: dict[str, int] = {}
    if station_names:
        station_rows = await conn.fetch(
            "SELECT name, MIN(id) AS id FROM stations WHERE name = ANY($1) GROUP BY name",
            station_names,
        )
        station_map = {str(row["name"]): int(row["id"]) for row in station_rows}

    values: list[
        tuple[str, str | None, int | None, str | None, int | None, str | None, int | None]
    ] = []
    for row in unique_rows:
        train_no = str(row.get("train_no") or "").strip()
        if not train_no:
            continue
        from_station = _to_text(row.get("from_station"))
        to_station = _to_text(row.get("to_station"))
        values.append(
            (
                train_no,
                _to_text(row.get("station_train_code")),
                station_map.get(from_station) if from_station else None,
                from_station,
                station_map.get(to_station) if to_station else None,
                to_station,
                _to_int(row.get("total_num")),
            )
        )
    return values


def _parse_stop_rows(train_no: str, rows: list[asyncpg.Record]) -> list[StopEvent]:
    events: list[StopEvent] = []
    previous_depart: int | None = None

    for row in rows:
        station_name = (row["station_name"] or "").strip()
        if not row["station_no"] or not station_name:
            continue

        base_minutes = int(row["arrive_day_diff"] or 0) * MINUTES_PER_DAY
        arrive_clock = parse_hhmm(row["arrive_time"])
        start_clock = parse_hhmm(row["start_time"])

        arrive_abs: int | None = None
        if arrive_clock is not None:
            arrive_abs = base_minutes + arrive_clock
        elif start_clock is not None:
            arrive_abs = base_minutes + start_clock

        depart_abs: int | None = None
        if start_clock is not None:
            depart_abs = base_minutes + start_clock
            if arrive_abs is not None:
                depart_abs = advance_past(depart_abs, arrive_abs)
        else:
            depart_abs = arrive_abs

        if previous_depart is not None:
            if arrive_abs is not None:
                arrive_abs = advance_past(arrive_abs, previous_depart)
            if depart_abs is not None:
                depart_abs = advance_past(depart_abs, previous_depart)

        if depart_abs is not None:
            previous_depart = depart_abs

        events.append(
            StopEvent(
                train_no=train_no,
                stop_number=int(row["station_no"]),
                station_name=station_name,
                train_code=(row["station_train_code"] or "").strip(),
                arrive_abs_min=arrive_abs,
                depart_abs_min=depart_abs,
            )
        )

    return events


def _make_seat_info(
    seat_type: str,
    status: str,
    available_count: int | None,
) -> SeatInfo:
    normalized = status.strip().lower()
    available = normalized == "available" and (
        available_count is None or available_count > 0
    )
    if available_count is not None and available_count > 0:
        display_status = str(available_count)
    else:
        display_status = AVAILABILITY_STATUS_MAP.get(normalized, "--")
    return SeatInfo(
        seat_type=seat_type.strip().lower(),
        status=display_status,
        price=None,
        available=available,
    )


def _to_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _to_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def _to_date(value: Any) -> date_type | None:
    if isinstance(value, date_type):
        return value

    text = str(value or "").strip()
    if not text:
        return None

    try:
        if len(text) == 8 and text.isdigit():
            return date_type.fromisoformat(f"{text[:4]}-{text[4:6]}-{text[6:]}")
        return date_type.fromisoformat(text)
    except ValueError:
        return None
