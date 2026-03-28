from __future__ import annotations

from pydantic import BaseModel


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
