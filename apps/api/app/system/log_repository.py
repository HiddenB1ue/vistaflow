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
