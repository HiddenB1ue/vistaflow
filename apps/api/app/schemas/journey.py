from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field, model_validator


class SeatSchema(BaseModel):
    seat_type: str
    status: str
    price: float | None
    available: bool


class JourneySegment(BaseModel):
    train_code: str
    from_station: str
    to_station: str
    departure_time: str  # "HH:mm"
    arrival_time: str    # "HH:mm"
    duration_minutes: int
    seats: list[SeatSchema]


class JourneyResult(BaseModel):
    id: str
    is_direct: bool
    total_duration_minutes: int
    departure_time: str
    arrival_time: str
    min_price: float | None
    segments: list[JourneySegment]


class JourneySearchRequest(BaseModel):
    from_station: str = Field(min_length=1)
    to_station: str = Field(min_length=1)
    date: date
    transfer_count: int = Field(default=0, ge=0, le=3)
    include_fewer_transfers: bool = True
    allowed_train_types: list[str] = Field(default_factory=list)
    excluded_train_types: list[str] = Field(default_factory=list)
    departure_time_start: time | None = None
    departure_time_end: time | None = None
    arrival_deadline: time | None = None
    min_transfer_minutes: int = Field(default=30, ge=0)
    max_transfer_minutes: int | None = Field(default=None, ge=0)
    filter_running_only: bool = False
    enable_ticket_enrich: bool = False
    display_limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_stations_differ(self) -> JourneySearchRequest:
        if self.from_station.strip() == self.to_station.strip():
            raise ValueError("出发站和到达站不能相同")
        return self


class JourneySearchResponse(BaseModel):
    journeys: list[JourneyResult]
    total: int
    date: str
