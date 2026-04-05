from __future__ import annotations

import itertools

import asyncpg

from app.database import BaseRepository
from app.models import SeatInfo, SeatLookupKey, StopEvent, Timetable
from app.planner.time_utils import advance_past, parse_hhmm


# ---------------------------------------------------------------------------
# StationRepository
# ---------------------------------------------------------------------------


class StationRepository(BaseRepository):
    async def find_all(self) -> list[dict[str, object]]:
        """返回所有站点完整字段。"""
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
        """批量 upsert 站点数据，返回写入条数。"""
        count = 0
        async with self._pool.acquire() as conn:
            for s in stations:
                await conn.execute(
                    """
                    INSERT INTO stations (telecode, name, pinyin, abbr, area_code)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (telecode) DO UPDATE
                    SET name = EXCLUDED.name,
                        pinyin = EXCLUDED.pinyin,
                        abbr = EXCLUDED.abbr,
                        area_code = EXCLUDED.area_code,
                        updated_at = NOW()
                    """,
                    s.get("telecode", ""),
                    s.get("name", ""),
                    s.get("pinyin", ""),
                    s.get("abbr", ""),
                    s.get("area_code", ""),
                )
                count += 1
        return count

    async def find_missing_geo(self) -> list[dict[str, object]]:
        """查询坐标缺失的站点。"""
        sql = """
            SELECT id, name, area_name
            FROM stations
            WHERE longitude IS NULL OR latitude IS NULL
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [dict(row) for row in rows]

    async def update_geo(
        self, station_id: int, longitude: float, latitude: float, geo_source: str
    ) -> None:
        """更新站点经纬度和来源。"""
        sql = """
            UPDATE stations
            SET longitude = $2, latitude = $3,
                geo_source = $4,
                geo_updated_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, station_id, longitude, latitude, geo_source)

    async def find_by_names(self, names: list[str]) -> list[dict[str, object]]:
        """按名称列表过滤站点。"""
        cleaned = [n.strip() for n in names if n.strip()]
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
        """批量查询站点 GCJ-02 坐标，返回 {站名: (longitude, latitude)}。"""
        cleaned = sorted({n.strip() for n in names if n.strip()})
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
        """模糊搜索站点（名称/拼音/简拼）。"""
        kw = keyword.strip()
        if not kw:
            return []

        sql = """
            SELECT name, telecode, pinyin, abbr
            FROM stations
            WHERE name    LIKE $1
               OR pinyin  LIKE $1
               OR abbr    LIKE $1
            ORDER BY
                CASE WHEN name = $2 THEN 0
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
                "name":    str(row["name"]),
                "telecode": str(row["telecode"] or ""),
                "pinyin":  str(row["pinyin"] or ""),
                "abbr":    str(row["abbr"] or ""),
            }
            for row in rows
        ]

    async def get_telecodes_by_names(
        self,
        names: set[str],
    ) -> dict[str, str]:
        """批量查询站点电报码，返回 {站名: 电报码}。"""
        cleaned = sorted({n.strip() for n in names if n.strip()})
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


# ---------------------------------------------------------------------------
# TrainRepository
# ---------------------------------------------------------------------------


class TrainRepository(BaseRepository):
    async def get_stops_by_train_code(
        self,
        train_code: str,
        from_station: str,
        to_station: str,
        full_route: bool = False,
    ) -> list[dict[str, object]]:
        """查询车次经停站列表。"""
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
        """找到同时经停 from_station 和 to_station 的 train_no。"""
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


def _slice_stops(
    stops: list[dict[str, object]],
    from_station: str,
    to_station: str,
) -> list[dict[str, object]]:
    """截取 from_station 到 to_station 之间的经停段。"""
    names = [str(s["station_name"]).strip() for s in stops]
    try:
        start_idx = names.index(from_station.strip())
        end_idx = names.index(to_station.strip())
    except ValueError:
        return []

    if start_idx <= end_idx:
        return stops[start_idx : end_idx + 1]
    return list(reversed(stops[end_idx : start_idx + 1]))


# ---------------------------------------------------------------------------
# TimetableRepository
# ---------------------------------------------------------------------------

MINUTES_PER_DAY = 1440


def _parse_stop_rows(train_no: str, rows: list[asyncpg.Record]) -> list[StopEvent]:
    """将数据库行转换为 StopEvent 列表，计算跨天绝对分钟数。"""
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


class TimetableRepository(BaseRepository):
    async def load_timetable(self, run_date: str, filter_running_only: bool) -> Timetable:
        """加载完整时刻表。

        filter_running_only=True 时只加载当日有开行记录（status='running'）的车次。
        """
        if filter_running_only:
            sql = """
                SELECT
                    ts.train_no,
                    ts.station_no,
                    COALESCE(ts.station_name, '')      AS station_name,
                    COALESCE(ts.station_train_code, '') AS station_train_code,
                    ts.arrive_time,
                    ts.start_time,
                    COALESCE(ts.arrive_day_diff, 0)    AS arrive_day_diff
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
                    COALESCE(ts.station_name, '')      AS station_name,
                    COALESCE(ts.station_train_code, '') AS station_train_code,
                    ts.arrive_time,
                    ts.start_time,
                    COALESCE(ts.arrive_day_diff, 0)    AS arrive_day_diff
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


# ---------------------------------------------------------------------------
# SeatRepository
# ---------------------------------------------------------------------------

AVAILABILITY_STATUS_MAP = {
    "available": "有",
    "waitlist": "候补",
    "sold_out": "无",
}


def _make_seat_info(seat_type: str, status: str, available_count: int | None) -> SeatInfo:
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


class SeatRepository(BaseRepository):
    async def load_segment_seats(
        self,
        run_date: str,
        segments: set[SeatLookupKey],
    ) -> dict[SeatLookupKey, list[SeatInfo]]:
        """批量查询指定区间的最新余票快照。"""
        if not segments:
            return {}

        # 构建 VALUES 子句用于批量匹配
        placeholders = ", ".join(
            f"(${i * 3 + 1}, ${i * 3 + 2}, ${i * 3 + 3})"
            for i in range(len(segments))
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
                    int(row["available_count"]) if row["available_count"] is not None else None
                ),
            )
            result.setdefault(key, []).append(seat)

        return result
