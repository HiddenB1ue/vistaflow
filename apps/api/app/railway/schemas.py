from __future__ import annotations

from pydantic import BaseModel

# --- Station schemas (from schemas/station.py) ---


class StationGeoItem(BaseModel):
    name: str
    longitude: float | None
    latitude: float | None
    found: bool


class StationGeoResponse(BaseModel):
    items: list[StationGeoItem]


class StationSuggestItem(BaseModel):
    name: str
    telecode: str
    pinyin: str
    abbr: str


class StationSuggestResponse(BaseModel):
    items: list[StationSuggestItem]


# --- Train schemas (from schemas/train.py) ---


class StopItem(BaseModel):
    station_name: str
    arrival_time: str | None    # "HH:mm"，始发站为 null
    departure_time: str | None  # "HH:mm"，终到站为 null
    stop_number: int


class TrainStopsResponse(BaseModel):
    train_code: str
    stops: list[StopItem]


# --- Station full response (extended) ---


class StationFullResponse(BaseModel):
    id: int
    name: str
    telecode: str
    pinyin: str | None = None
    abbr: str | None = None
    areaCode: str | None = None
    areaName: str | None = None
    countryCode: str | None = None
    countryName: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    geoSource: str | None = None
    geoUpdatedAt: str | None = None
