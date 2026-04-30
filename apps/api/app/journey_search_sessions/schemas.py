from __future__ import annotations

from datetime import date, datetime, time
from math import ceil
from typing import Literal

from pydantic import BaseModel, Field

from app.journeys.schemas import JourneySearchRequest

TicketStatus = Literal["ready", "partial", "unavailable", "disabled"]
SegmentTicketStatus = Literal["ready", "unavailable", "disabled"]
JourneySortMode = Literal["duration", "departure", "price"]


class SeatInfoEntry(BaseModel):
    seat_type: str
    status: str
    price: float | None = None
    available: bool = False


class PriceCacheEntry(BaseModel):
    min_price: float | None = None
    seats: list[SeatInfoEntry] = Field(default_factory=list)
    matched_by: str = ""
    failed: bool = False


def price_map_key(train_no: str, from_station: str, to_station: str) -> str:
    return f"{train_no}:{from_station}:{to_station}"


class SearchSessionViewRequest(BaseModel):
    sort_by: JourneySortMode = Field(default="duration")
    exclude_direct_train_codes_in_transfer_routes: bool = Field(default=False)
    display_train_types: list[str] = Field(default_factory=list)
    transfer_counts: list[int] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    include_tickets: bool = Field(default=True)


class SearchSessionCreateRequest(BaseModel):
    from_station: str = Field(min_length=1)
    to_station: str = Field(min_length=1)
    date: date
    transfer_count: int = Field(default=2, ge=0, le=3)
    include_fewer_transfers: bool = Field(default=True)
    allowed_train_types: list[str] = Field(default_factory=list)
    excluded_train_types: list[str] = Field(default_factory=list)
    allowed_trains: list[str] = Field(default_factory=list)
    excluded_trains: list[str] = Field(default_factory=list)
    departure_time_start: time | None = None
    departure_time_end: time | None = None
    arrival_deadline: time | None = None
    min_transfer_minutes: int = Field(default=30, ge=0)
    max_transfer_minutes: int | None = Field(default=None, ge=0)
    allowed_transfer_stations: list[str] = Field(default_factory=list)
    excluded_transfer_stations: list[str] = Field(default_factory=list)
    filter_running_only: bool = Field(default=True)
    view: SearchSessionViewRequest | None = None

    def to_journey_request(self) -> JourneySearchRequest:
        return JourneySearchRequest(
            from_station=self.from_station,
            to_station=self.to_station,
            date=self.date,
            transfer_count=self.transfer_count,
            include_fewer_transfers=self.include_fewer_transfers,
            allowed_train_types=self.allowed_train_types,
            excluded_train_types=self.excluded_train_types,
            allowed_trains=self.allowed_trains,
            excluded_trains=self.excluded_trains,
            departure_time_start=self.departure_time_start,
            departure_time_end=self.departure_time_end,
            arrival_deadline=self.arrival_deadline,
            min_transfer_minutes=self.min_transfer_minutes,
            max_transfer_minutes=self.max_transfer_minutes,
            allowed_transfer_stations=self.allowed_transfer_stations,
            excluded_transfer_stations=self.excluded_transfer_stations,
            filter_running_only=self.filter_running_only,
        )


class RoutePointResponse(BaseModel):
    lng: float
    lat: float


class RouteStationResponse(BaseModel):
    name: str
    code: str = ""
    city: str = ""
    lng: float
    lat: float


class RouteSeatResponse(BaseModel):
    type: str
    label: str
    price: float | None
    available: bool
    availabilityText: str | None = None


class RouteStopResponse(BaseModel):
    station: RouteStationResponse
    arrivalTime: str | None = None
    departureTime: str | None = None
    stopDuration: int | None = None


class CachedTrainSegment(BaseModel):
    trainNo: str
    no: str
    origin: RouteStationResponse
    destination: RouteStationResponse
    departureDate: str
    departureTime: str
    arrivalDate: str
    arrivalTime: str
    stopsCount: int | None = None


class RouteTrainSegmentResponse(CachedTrainSegment):
    stops: list[RouteStopResponse] = Field(default_factory=list)
    seats: list[RouteSeatResponse] = Field(default_factory=list)
    ticketStatus: SegmentTicketStatus = "disabled"


class RouteTransferSegmentResponse(BaseModel):
    transfer: str


class RouteResponse(BaseModel):
    id: str
    trainNo: str
    type: str
    origin: RouteStationResponse
    destination: RouteStationResponse
    departureDate: str
    departureTime: str
    arrivalDate: str
    arrivalTime: str
    durationMinutes: int
    segs: list[RouteTrainSegmentResponse | RouteTransferSegmentResponse]
    pathPoints: list[RoutePointResponse]
    ticketStatus: TicketStatus = "disabled"


class SearchSummaryResponse(BaseModel):
    fromStation: str
    toStation: str
    date: str
    totalCandidates: int


class SearchSessionAvailableFacetsResponse(BaseModel):
    transferCounts: list[int] = Field(default_factory=list)
    trainTypes: list[str] = Field(default_factory=list)


class SearchSessionViewResponse(BaseModel):
    sortBy: JourneySortMode
    excludeDirectTrainCodesInTransferRoutes: bool
    displayTrainTypes: list[str]
    transferCounts: list[int]
    page: int
    pageSize: int
    includeTickets: bool


class SearchSessionViewResultResponse(BaseModel):
    items: list[RouteResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    appliedView: SearchSessionViewResponse
    availableFacets: SearchSessionAvailableFacetsResponse

    @classmethod
    def build(
        cls,
        *,
        items: list[RouteResponse],
        total: int,
        view: SearchSessionViewResponse,
        facets: SearchSessionAvailableFacetsResponse,
    ) -> SearchSessionViewResultResponse:
        total_pages = ceil(total / view.pageSize) if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=view.page,
            pageSize=view.pageSize,
            totalPages=total_pages,
            appliedView=view,
            availableFacets=facets,
        )


class SearchSessionCreateResponse(BaseModel):
    searchId: str
    expiresAt: datetime
    searchSummary: SearchSummaryResponse
    viewResult: SearchSessionViewResultResponse


class SearchSessionSummaryResponse(BaseModel):
    searchId: str
    expiresAt: datetime
    searchSummary: SearchSummaryResponse


class SearchSessionDeleteResponse(BaseModel):
    deleted: bool


class CachedRouteCandidate(BaseModel):
    id: str
    trainNo: str
    type: str
    origin: RouteStationResponse
    destination: RouteStationResponse
    departureDate: str
    departureTime: str
    arrivalDate: str
    arrivalTime: str
    durationMinutes: int
    segs: list[CachedTrainSegment | RouteTransferSegmentResponse]
    pathPoints: list[RoutePointResponse]
    isDirect: bool
    transferCount: int
    trainTypes: list[str] = Field(default_factory=list)
    trainCodes: list[str] = Field(default_factory=list)
