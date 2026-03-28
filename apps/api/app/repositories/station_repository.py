from __future__ import annotations

from app.repositories.base import BaseRepository


class StationRepository(BaseRepository):
    async def get_geo_by_names(
        self,
        names: list[str],
    ) -> dict[str, tuple[float, float]]:
        """批量查询站点 GCJ-02 坐标，返回 {站名: (longitude, latitude)}。

        只返回有坐标数据的站点，未找到的站点不出现在结果中。
        """
        cleaned = sorted({n.strip() for n in names if n.strip()})
        if not cleaned:
            return {}

        sql = """
            SELECT DISTINCT ON (name)
                name,
                longitude,
                latitude
            FROM stations
            WHERE name = ANY($1)
              AND longitude IS NOT NULL
              AND latitude IS NOT NULL
            ORDER BY name, geo_updated_at DESC NULLS LAST, id DESC
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, cleaned)

        return {
            str(row["name"]): (float(row["longitude"]), float(row["latitude"]))
            for row in rows
        }

    async def suggest_by_keyword(
        self,
        keyword: str,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        """模糊搜索站点（名称/拼音/简拼），返回 [{name, telecode, pinyin, abbr}] 列表。"""
        kw = keyword.strip()
        if not kw:
            return []

        sql = """
            SELECT name, telecode, pinyin, abbr
            FROM stations
            WHERE name    LIKE $1
               OR pinyin  LIKE $1
               OR abbr    LIKE $1
            ORDER BY
                CASE WHEN name = $2 THEN 0
                     WHEN name LIKE $2 || '%' THEN 1
                     WHEN abbr = $2 THEN 2
                     ELSE 3
                END,
                name
            LIMIT $3
        """

        pattern = f"%{kw}%"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, pattern, kw, limit)

        return [
            {
                "name":    str(row["name"]),
                "telecode": str(row["telecode"] or ""),
                "pinyin":  str(row["pinyin"] or ""),
                "abbr":    str(row["abbr"] or ""),
            }
            for row in rows
        ]

    async def get_telecodes_by_names(
        self,
        names: set[str],
    ) -> dict[str, str]:
        """批量查询站点电报码，返回 {站名: 电报码}。

        用于 12306 票价查询时的站点匹配。
        """
        cleaned = sorted({n.strip() for n in names if n.strip()})
        if not cleaned:
            return {}

        sql = """
            SELECT name, telecode
            FROM stations
            WHERE name = ANY($1)
              AND telecode IS NOT NULL
              AND telecode <> ''
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, cleaned)

        return {str(row["name"]): str(row["telecode"]) for row in rows}
