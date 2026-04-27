from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.database import BaseRepository


@dataclass
class DailyCount:
    date: date
    count: int


@dataclass
class ActiveTaskRecord:
    id: int
    name: str
    status: str
    started_at: datetime | None


@dataclass
class AlertRecord:
    id: int
    severity: str
    message: str
    created_at: datetime


class OverviewRepository(BaseRepository):
    """Repository for aggregating overview statistics."""

    async def count_total_records(self) -> int:
        """Count total records across stations, trains, train_stops, train_runs tables."""
        query = """
            SELECT 
                (SELECT COUNT(*) FROM stations) +
                (SELECT COUNT(*) FROM trains) +
                (SELECT COUNT(*) FROM train_stops) +
                (SELECT COUNT(*) FROM train_runs) AS total
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query)
            return row["total"] if row else 0

    async def count_stations_with_coordinates(self) -> tuple[int, int]:
        """Return (stations_with_coords, total_stations)."""
        query = """
            SELECT 
                COUNT(*) FILTER (
                    WHERE longitude IS NOT NULL AND latitude IS NOT NULL
                ) AS with_coords,
                COUNT(*) AS total
            FROM stations
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query)
            if row:
                return (row["with_coords"], row["total"])
            return (0, 0)

    async def count_daily_records(self, days: int) -> list[DailyCount]:
        """Return daily record counts for the past N days."""
        query = """
            WITH date_series AS (
                SELECT generate_series(
                    CURRENT_DATE - $1::int + 1,
                    CURRENT_DATE,
                    '1 day'::interval
                )::date AS day
            )
            SELECT 
                ds.day,
                COALESCE(
                    (SELECT COUNT(*) FROM stations WHERE DATE(created_at) = ds.day) +
                    (SELECT COUNT(*) FROM trains WHERE DATE(created_at) = ds.day) +
                    (SELECT COUNT(*) FROM train_stops WHERE DATE(created_at) = ds.day) +
                    (SELECT COUNT(*) FROM train_runs WHERE DATE(created_at) = ds.day),
                    0
                ) AS count
            FROM date_series ds
            ORDER BY ds.day
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, days)
            return [DailyCount(date=row["day"], count=row["count"]) for row in rows]

    async def count_today_record_changes(self) -> int:
        """Count records created or updated today across core data tables."""
        query = """
            SELECT
                (SELECT COUNT(*) FROM stations WHERE DATE(updated_at) = CURRENT_DATE) +
                (SELECT COUNT(*) FROM trains WHERE DATE(updated_at) = CURRENT_DATE) +
                (SELECT COUNT(*) FROM train_stops WHERE DATE(updated_at) = CURRENT_DATE) +
                (SELECT COUNT(*) FROM train_runs WHERE DATE(updated_at) = CURRENT_DATE) AS total
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query)
            return row["total"] if row else 0

    async def get_active_tasks(self, limit: int = 5) -> list[ActiveTaskRecord]:
        """Return tasks with status 'running' or 'pending'."""
        query = """
            SELECT id, name, status, latest_run_started_at
            FROM task
            WHERE status IN ('running') OR latest_run_status IN ('running', 'pending')
            ORDER BY latest_run_started_at DESC NULLS LAST
            LIMIT $1
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [
                ActiveTaskRecord(
                    id=row["id"],
                    name=row["name"],
                    status=row["status"],
                    started_at=row["latest_run_started_at"],
                )
                for row in rows
            ]

    async def get_recent_alerts(self, limit: int = 3) -> list[AlertRecord]:
        """Return recent system alerts from log table."""
        query = """
            SELECT id, severity, message, created_at
            FROM log
            WHERE severity IN ('WARN', 'ERROR', 'SUCCESS', 'INFO')
            ORDER BY created_at DESC
            LIMIT $1
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [
                AlertRecord(
                    id=row["id"],
                    severity=row["severity"],
                    message=row["message"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def count_todays_task_runs(self) -> int:
        """Count task runs created today."""
        query = """
            SELECT COUNT(*) AS count
            FROM task_run
            WHERE DATE(created_at) = CURRENT_DATE
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query)
            return row["count"] if row else 0
