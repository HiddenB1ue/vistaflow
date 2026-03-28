from __future__ import annotations

from app.domain.models import SeatInfo
from app.domain.types import SeatLookupKey
from app.repositories.base import BaseRepository

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
