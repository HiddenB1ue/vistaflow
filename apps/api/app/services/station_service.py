from __future__ import annotations

from app.repositories.station_repository import StationRepository
from app.schemas.station import (
    StationGeoItem,
    StationGeoResponse,
    StationSuggestItem,
    StationSuggestResponse,
)


class StationService:
    def __init__(self, repo: StationRepository) -> None:
        self._repo = repo

    async def get_geo(self, names: list[str]) -> StationGeoResponse:
        cleaned = [n.strip() for n in names if n.strip()]
        if not cleaned:
            return StationGeoResponse(items=[])

        geo_map = await self._repo.get_geo_by_names(cleaned)

        items = [
            StationGeoItem(
                name=name,
                longitude=geo_map[name][0] if name in geo_map else None,
                latitude=geo_map[name][1] if name in geo_map else None,
                found=name in geo_map,
            )
            for name in cleaned
        ]
        return StationGeoResponse(items=items)

    async def suggest(self, keyword: str, limit: int = 10) -> StationSuggestResponse:
        rows = await self._repo.suggest_by_keyword(keyword, limit)
        items = [
            StationSuggestItem(
                name=row["name"],
                telecode=row["telecode"],
                pinyin=row["pinyin"],
                abbr=row["abbr"],
            )
            for row in rows
        ]
        return StationSuggestResponse(items=items)
