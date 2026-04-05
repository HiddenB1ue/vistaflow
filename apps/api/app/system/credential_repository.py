from __future__ import annotations

from app.database import BaseRepository
from app.models import Credential


class CredentialRepository(BaseRepository):
    async def find_all(self) -> list[Credential]:
        sql = """
            SELECT id, name, description, raw_key, quota_info,
                   expires_at, created_at, updated_at
            FROM credential
            ORDER BY id
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [
            Credential(
                id=row["id"],
                name=row["name"],
                description=row.get("description"),
                raw_key=row["raw_key"],
                quota_info=row.get("quota_info"),
                expires_at=row.get("expires_at"),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]
