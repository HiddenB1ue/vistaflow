from __future__ import annotations

from datetime import date, time
from typing import Literal

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
    # Basic search parameters
    from_station: str = Field(min_length=1)
    to_station: str = Field(min_length=1)
    date: date
    transfer_count: int = Field(default=2, ge=0, le=3)
    include_fewer_transfers: bool = Field(default=True)
    
    # Train filtering
    allowed_train_types: list[str] = Field(default_factory=list)
    excluded_train_types: list[str] = Field(default_factory=list)
    allowed_trains: list[str] = Field(default_factory=list)
    excluded_trains: list[str] = Field(default_factory=list)
    
    # Time constraints
    departure_time_start: time | None = None
    departure_time_end: time | None = None
    arrival_deadline: time | None = None
    
    # Transfer constraints
    min_transfer_minutes: int = Field(default=30, ge=0)
    max_transfer_minutes: int | None = Field(default=None, ge=0)
    allowed_transfer_stations: list[str] = Field(default_factory=list)
    excluded_transfer_stations: list[str] = Field(default_factory=list)
    
    # Sorting and display
    sort_by: Literal["duration", "price", "departure"] = Field(default="duration")
    train_sequence_top_n: int = Field(default=3, ge=0, le=10)
    display_limit: int = Field(default=50, ge=1, le=100)
    display_train_types: list[str] = Field(default_factory=list)
    
    # Optimization options
    exclude_direct_train_codes_in_transfer_routes: bool = Field(default=True)
    filter_running_only: bool = Field(default=True)
    enable_ticket_enrich: bool = Field(default=True)

    @model_validator(mode="after")
    def validate_stations_differ(self) -> JourneySearchRequest:
        if self.from_station.strip() == self.to_station.strip():
            raise ValueError("出发站和到达站不能相同")
        return self


class JourneySearchResponse(BaseModel):
    journeys: list[JourneyResult]
    total: int
    date: str
