from __future__ import annotations

import asyncpg


class BaseRepository:
    """所有 Repository 的基类，持有 asyncpg 连接池。"""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
