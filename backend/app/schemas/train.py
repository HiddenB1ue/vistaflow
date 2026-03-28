from __future__ import annotations

from pydantic import BaseModel


class StopItem(BaseModel):
    station_name: str
    arrival_time: str | None    # "HH:mm"，始发站为 null
    departure_time: str | None  # "HH:mm"，终到站为 null
    stop_number: int


class TrainStopsResponse(BaseModel):
    train_code: str
    stops: list[StopItem]
