from __future__ import annotations

from app.database import BaseRepository
from app.models import SystemSetting


class SystemSettingRepository(BaseRepository):
    async def find_all(self) -> list[SystemSetting]:
        sql = """
            SELECT id, key, value, value_type, category, label, description, enabled, created_at, updated_at
            FROM system_setting
            ORDER BY
                CASE category
                    WHEN 'amap' THEN 1
                    WHEN 'ticket_12306' THEN 2
                    WHEN 'task' THEN 3
                    WHEN 'system' THEN 4
                    ELSE 99
                END,
                id
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [self._row_to_setting(row) for row in rows]

    async def find_by_key(self, key: str) -> SystemSetting | None:
        sql = """
            SELECT id, key, value, value_type, category, label, description, enabled, created_at, updated_at
            FROM system_setting
            WHERE key = $1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, key)
        return self._row_to_setting(row) if row is not None else None

    async def find_by_keys(self, keys: list[str]) -> list[SystemSetting]:
        sql = """
            SELECT id, key, value, value_type, category, label, description, enabled, created_at, updated_at
            FROM system_setting
            WHERE key = ANY($1)
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, keys)
        return [self._row_to_setting(row) for row in rows]

    async def update_settings(
        self,
        items: list[tuple[str, str, bool]],
    ) -> list[SystemSetting]:
        sql = """
            UPDATE system_setting
            SET value = $2,
                enabled = $3,
                updated_at = NOW()
            WHERE key = $1
            RETURNING id, key, value, value_type, category, label, description, enabled, created_at, updated_at
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                rows = []
                for key, value, enabled in items:
                    row = await conn.fetchrow(sql, key, value, enabled)
                    if row is None:
                        raise RuntimeError(f"Failed to update system setting {key}")
                    rows.append(row)
        return [self._row_to_setting(row) for row in rows]

    @staticmethod
    def _row_to_setting(row: object) -> SystemSetting:
        return SystemSetting(
            id=row["id"],
            key=str(row["key"]),
            value=str(row["value"]),
            value_type=str(row["value_type"]),
            category=str(row["category"]),
            label=str(row["label"]),
            description=str(row["description"]) if row["description"] is not None else None,
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
