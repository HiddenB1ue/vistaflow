from __future__ import annotations

from app.repositories.train_repository import TrainRepository
from app.schemas.train import StopItem, TrainStopsResponse
from app.services.exceptions import NotFoundError


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
                stop_number=int(row["stop_number"]),  # type: ignore[arg-type]
            )
            for row in rows
        ]
        return TrainStopsResponse(train_code=train_code, stops=stops)
