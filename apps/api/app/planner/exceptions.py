"""Custom exceptions for the planner module."""

from __future__ import annotations


class PlannerError(Exception):
    """Base exception for planner-related errors."""

    pass


class NoTimetableDataError(PlannerError):
    """Raised when no timetable data is available for the requested date."""

    def __init__(self, run_date: str) -> None:
        self.run_date = run_date
        super().__init__(f"No timetable data available for date: {run_date}")


class InvalidQueryError(PlannerError):
    """Raised when query parameters are invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Invalid query: {message}")


class NoRoutesFoundError(PlannerError):
    """Raised when no routes are found matching the criteria."""

    def __init__(self, from_station: str, to_station: str) -> None:
        self.from_station = from_station
        self.to_station = to_station
        super().__init__(
            f"No routes found from {from_station} to {to_station} with given criteria"
        )
