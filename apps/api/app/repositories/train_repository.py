from __future__ import annotations

from app.repositories.base import BaseRepository


class TrainRepository(BaseRepository):
    async def get_stops_by_train_code(
        self,
        train_code: str,
        from_station: str,
        to_station: str,
        full_route: bool = False,
    ) -> list[dict[str, object]]:
        """查询车次经停站列表。

        先解析 train_code 对应的 train_no（同一 train_code 可能有多个 train_no），
        再按站序返回经停站信息。full_route=False 时只返回 from_station 到 to_station 之间的区间。
        """
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
