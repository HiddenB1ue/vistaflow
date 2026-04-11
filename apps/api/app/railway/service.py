from __future__ import annotations

from typing import Any

from app.exceptions import NotFoundError
from app.railway.repository import StationRepository, TrainRepository
from app.railway.schemas import (
    StationFullResponse,
    StationGeoItem,
    StationGeoResponse,
    StationSuggestItem,
    StationSuggestResponse,
    StopItem,
    TrainStopsResponse,
)


def _row_to_station_full(row: dict[str, Any]) -> StationFullResponse:
    def opt_str(key: str) -> str | None:
        v = row.get(key)
        return str(v) if v is not None else None

    return StationFullResponse(
        id=int(row["id"]),
        name=str(row["name"]),
        telecode=str(row["telecode"]),
        pinyin=opt_str("pinyin"),
        abbr=opt_str("abbr"),
        areaCode=opt_str("area_code"),
        areaName=opt_str("area_name"),
        countryCode=opt_str("country_code"),
        countryName=opt_str("country_name"),
        longitude=float(row["longitude"]) if row.get("longitude") is not None else None,
        latitude=float(row["latitude"]) if row.get("latitude") is not None else None,
        geoSource=opt_str("geo_source"),
        geoUpdatedAt=(
            row["geo_updated_at"].isoformat() if row.get("geo_updated_at") else None
        ),
    )


class StationService:
    def __init__(self, repo: StationRepository) -> None:
        self._repo = repo

    async def list_stations(
        self, names: list[str] | None = None
    ) -> list[StationFullResponse]:
        rows = await (
            self._repo.find_by_names(names) if names else self._repo.find_all()
        )
        return [_row_to_station_full(row) for row in rows]

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

    async def get_all_for_cache(self) -> StationSuggestResponse:
        """获取所有车站的简化信息，用于前端缓存"""
        rows = await self._repo.find_all_for_cache()
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


class TrainService:
    def __init__(self, repo: TrainRepository) -> None:
        self._repo = repo

    async def get_stops(
        self,
        train_code: str,
        from_station: str,
        to_station: str,
        full_route: bool = False,
    ) -> TrainStopsResponse:
        rows = await self._repo.get_stops_by_train_code(
            train_code=train_code,
            from_station=from_station,
            to_station=to_station,
            full_route=full_route,
        )
        if not rows:
            raise NotFoundError(f"未找到车次 {train_code} 的经停信息")

        stops = [
            StopItem(
                station_name=str(row["station_name"]),
                arrival_time=str(row["arrival_time"]) if row["arrival_time"] else None,
                departure_time=str(row["departure_time"]) if row["departure_time"] else None,
                stop_number=int(str(row["stop_number"])),
            )
            for row in rows
        ]
        return TrainStopsResponse(train_code=train_code, stops=stops)
