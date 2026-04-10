"""Query compilation and validation for journey search.

This module provides query compilation functionality to standardize and validate
user input parameters before executing the journey search algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

from app.journeys.schemas import JourneySearchRequest


@dataclass(frozen=True)
class CompiledQuery:
    """Compiled and validated query parameters.
    
    All string fields are normalized (uppercase for train identifiers/types,
    stripped whitespace). Derived fields like cross_day and transfer_values
    are pre-computed.
    """
    
    # Basic search parameters
    from_station: str
    to_station: str
    run_date: str
    
    # Normalized train identifiers (uppercase, no whitespace)
    allowed_train_tokens: set[str]
    excluded_train_tokens: set[str]
    
    # Normalized train type prefixes (uppercase, no whitespace)
    allowed_train_type_prefixes: tuple[str, ...]
    excluded_train_type_prefixes: set[str]
    
    # Normalized station names (no whitespace)
    allowed_transfer_stations: set[str]
    excluded_transfer_stations: set[str]
    
    # Time constraints
    departure_time_start_min: int | None
    departure_time_end_min: int | None
    departure_time_cross_day: bool
    arrival_deadline_abs_min: int | None
    
    # Transfer constraints
    min_transfer_minutes: int
    max_transfer_minutes: int | None
    transfer_values: list[int]  # e.g., [0, 1, 2] or [2]
    
    # Sorting and display
    sort_by: str  # "duration" | "price" | "departure"
    train_sequence_top_n: int
    display_limit: int
    
    # Optimization options
    exclude_direct_train_codes_in_transfer_routes: bool
    display_train_types: set[str]
    filter_running_only: bool
    enable_ticket_enrich: bool


def _time_to_abs_min(t: time | None) -> int | None:
    """Convert time to absolute minutes from midnight."""
    if t is None:
        return None
    return t.hour * 60 + t.minute


def _arrival_deadline_to_abs_min(run_date: date, deadline: time | None) -> int | None:
    """Convert arrival deadline to absolute minutes.
    
    Assumes deadline can be on the next day (up to 48 hours from run_date midnight).
    """
    if deadline is None:
        return None
    
    deadline_min = deadline.hour * 60 + deadline.minute
    
    # If deadline is before 06:00, assume it's next day
    if deadline_min < 360:  # 06:00 = 360 minutes
        return 1440 + deadline_min  # Add 24 hours
    
    return deadline_min


def compile_query(req: JourneySearchRequest) -> CompiledQuery:
    """Compile and validate query parameters from request.
    
    Transformation rules:
    - All train identifiers converted to uppercase and stripped
    - All train type prefixes converted to uppercase and stripped
    - All station names stripped
    - max_transfer_minutes <= 0 converted to None
    - cross_day flag computed from time window
    - transfer_values list generated based on include_fewer_transfers
    
    Args:
        req: Journey search request with user input
    
    Returns:
        CompiledQuery with all normalized and validated parameters
    """
    # Normalize train identifiers (uppercase, strip whitespace)
    allowed_train_tokens = {
        item.strip().upper() for item in req.allowed_trains if item.strip()
    }
    excluded_train_tokens = {
        item.strip().upper() for item in req.excluded_trains if item.strip()
    }
    
    # Normalize train type prefixes (uppercase, strip whitespace)
    allowed_train_type_prefixes = tuple(
        sorted({item.strip().upper() for item in req.allowed_train_types if item.strip()})
    )
    excluded_train_type_prefixes = {
        item.strip().upper() for item in req.excluded_train_types if item.strip()
    }
    
    # Normalize station names (strip whitespace)
    allowed_transfer_station_set = {
        item.strip() for item in req.allowed_transfer_stations if item.strip()
    }
    excluded_transfer_station_set = {
        item.strip() for item in req.excluded_transfer_stations if item.strip()
    }
    
    # Normalize display train types (uppercase, strip whitespace)
    display_train_type_set = {
        item.strip().upper() for item in req.display_train_types if item.strip()
    }
    
    # Convert time constraints
    departure_time_start_min = _time_to_abs_min(req.departure_time_start)
    departure_time_end_min = _time_to_abs_min(req.departure_time_end)
    arrival_deadline_abs_min = _arrival_deadline_to_abs_min(req.date, req.arrival_deadline)
    
    # Compute cross_day flag
    departure_time_cross_day = (
        departure_time_start_min is not None
        and departure_time_end_min is not None
        and departure_time_start_min > departure_time_end_min
    )
    
    # Normalize max_transfer_minutes (<= 0 means unlimited)
    effective_max_transfer_minutes = (
        req.max_transfer_minutes if req.max_transfer_minutes and req.max_transfer_minutes > 0 else None
    )
    
    # Generate transfer_values list
    if req.include_fewer_transfers:
        transfer_values = list(range(0, req.transfer_count + 1))
    else:
        transfer_values = [req.transfer_count]
    
    return CompiledQuery(
        from_station=req.from_station.strip(),
        to_station=req.to_station.strip(),
        run_date=req.date.isoformat(),
        allowed_train_tokens=allowed_train_tokens,
        excluded_train_tokens=excluded_train_tokens,
        allowed_train_type_prefixes=allowed_train_type_prefixes,
        excluded_train_type_prefixes=excluded_train_type_prefixes,
        allowed_transfer_stations=allowed_transfer_station_set,
        excluded_transfer_stations=excluded_transfer_station_set,
        departure_time_start_min=departure_time_start_min,
        departure_time_end_min=departure_time_end_min,
        departure_time_cross_day=departure_time_cross_day,
        arrival_deadline_abs_min=arrival_deadline_abs_min,
        min_transfer_minutes=req.min_transfer_minutes,
        max_transfer_minutes=effective_max_transfer_minutes,
        transfer_values=transfer_values,
        sort_by=req.sort_by,
        train_sequence_top_n=req.train_sequence_top_n,
        display_limit=req.display_limit,
        exclude_direct_train_codes_in_transfer_routes=req.exclude_direct_train_codes_in_transfer_routes,
        display_train_types=display_train_type_set,
        filter_running_only=req.filter_running_only,
        enable_ticket_enrich=req.enable_ticket_enrich,
    )
