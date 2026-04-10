from __future__ import annotations

from app.database import BaseRepository
from app.models import LogRecord


class LogRepository(BaseRepository):
    async def find_all(self, limit: int = 100) -> list[LogRecord]:
        sql = """
            SELECT id, severity, message, highlighted_terms, created_at
            FROM log
            ORDER BY created_at DESC
            LIMIT $1
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, limit)
        return [
            LogRecord(
                id=row["id"],
                severity=row["severity"],
                message=row["message"],
                highlighted_terms=row.get("highlighted_terms"),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def find_logs_paginated(
        self,
        *,
        page: int,
        page_size: int,
        keyword: str = "",
        severity: str = "all",
    ) -> tuple[list[LogRecord], int]:
        """Find logs with pagination, filtering, and search.

        Returns (items, total_count)
        """
        # Build WHERE clause
        where_conditions = []
        params: list[str | int] = []
        param_idx = 1

        if keyword:
            where_conditions.append(
                f"(CAST(created_at AS TEXT) ILIKE ${param_idx} "
                f"OR severity ILIKE ${param_idx} "
                f"OR message ILIKE ${param_idx})"
            )
            params.append(f"%{keyword}%")
            param_idx += 1

        if severity != "all":
            where_conditions.append(f"severity = ${param_idx}")
            params.append(severity)
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

        # Query with COUNT(*) OVER() for efficient total count
        sql = f"""
            SELECT 
                id, 
                severity, 
                message, 
                highlighted_terms, 
                created_at,
                COUNT(*) OVER() as total_count
            FROM log
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([page_size, (page - 1) * page_size])

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        if not rows:
            return [], 0

        total = rows[0]["total_count"]
        items = [
            LogRecord(
                id=row["id"],
                severity=row["severity"],
                message=row["message"],
                highlighted_terms=row.get("highlighted_terms"),
                created_at=row["created_at"],
            )
            for row in rows
        ]
        return items, total

    async def write_log(
        self,
        severity: str,
        message: str,
        *,
        highlighted_terms: list[str] | None = None,
    ) -> None:
        sql = """
            INSERT INTO log (severity, message, highlighted_terms)
            VALUES ($1, $2, $3)
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, severity, message, highlighted_terms)
