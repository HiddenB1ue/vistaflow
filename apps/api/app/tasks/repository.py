from __future__ import annotations

from datetime import datetime

from app.database import BaseRepository
from app.models import CrawlTask


class TaskRepository(BaseRepository):
    async def find_all(self) -> list[CrawlTask]:
        sql = """
            SELECT id, name, type, type_label, status, description, cron,
                   metrics_label, metrics_value, timing_label, timing_value,
                   error_message, created_at, updated_at
            FROM task
            ORDER BY updated_at DESC
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [self._row_to_model(row) for row in rows]

    async def find_by_id(self, task_id: int) -> CrawlTask | None:
        sql = """
            SELECT id, name, type, type_label, status, description, cron,
                   metrics_label, metrics_value, timing_label, timing_value,
                   error_message, created_at, updated_at
            FROM task
            WHERE id = $1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, task_id)
        if row is None:
            return None
        return self._row_to_model(row)

    async def update_status(
        self,
        task_id: int,
        status: str,
        *,
        error_message: str | None = None,
        metrics_value: str | None = None,
        timing_value: str | None = None,
    ) -> None:
        sql = """
            UPDATE task
            SET status = $2,
                error_message = COALESCE($3, error_message),
                metrics_value = COALESCE($4, metrics_value),
                timing_value = COALESCE($5, timing_value),
                updated_at = NOW()
            WHERE id = $1
        """
        async with self._pool.acquire() as conn:
            await conn.execute(
                sql, task_id, status, error_message, metrics_value, timing_value
            )

    @staticmethod
    def _row_to_model(row: object) -> CrawlTask:
        r: dict = dict(row)  # type: ignore[arg-type]
        return CrawlTask(
            id=r["id"],
            name=r["name"],
            type=r["type"],
            type_label=r["type_label"],
            status=r["status"],
            description=r.get("description"),
            cron=r.get("cron"),
            metrics_label=r.get("metrics_label", ""),
            metrics_value=r.get("metrics_value", ""),
            timing_label=r.get("timing_label", ""),
            timing_value=r.get("timing_value", ""),
            error_message=r.get("error_message"),
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
