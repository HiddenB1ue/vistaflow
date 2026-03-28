from __future__ import annotations

import itertools

import asyncpg

from app.domain.models import StopEvent
from app.domain.types import Timetable
from app.planner.time_utils import advance_past, parse_hhmm
from app.repositories.base import BaseRepository

MINUTES_PER_DAY = 1440


def _parse_stop_rows(train_no: str, rows: list[asyncpg.Record]) -> list[StopEvent]:  # type: ignore[type-arg]
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
            params: tuple = (run_date,)
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
        for train_no, group in itertools.groupby(rows, key=lambda r: str(r["train_no"] or "").strip()):
            if not train_no:
                continue
            events = _parse_stop_rows(train_no, list(group))
            if len(events) >= 2:
                timetable[train_no] = events

        return timetable
