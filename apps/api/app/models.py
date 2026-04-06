from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


@dataclass(frozen=True)
class StopEvent:
    """时刻表中的单个经停事件。"""

    train_no: str
    stop_number: int
    station_name: str
    train_code: str
    arrive_abs_min: int | None
    depart_abs_min: int | None


@dataclass(frozen=True)
class Segment:
    """行程中的一段单趟列车。"""

    train_no: str
    train_code: str
    from_station: str
    to_station: str
    depart_abs_min: int
    arrive_abs_min: int


@dataclass(frozen=True)
class SeatInfo:
    """席别余票信息。"""

    seat_type: str
    status: str
    price: float | None
    available: bool


Timetable = dict[str, list["StopEvent"]]
StationIndex = dict[str, list[tuple[str, int]]]
SeatLookupKey = tuple[str, str, str]


TaskType = Literal[
    "fetch-station",
    "fetch-trains",
    "fetch-train-stops",
    "fetch-train-runs",
    "price",
]
TaskStatus = Literal["idle", "running", "completed", "error", "terminated"]
TaskRunStatus = Literal["pending", "running", "completed", "error", "terminated"]
TaskTriggerMode = Literal["manual"]
LogSeverity = Literal["SUCCESS", "INFO", "WARN", "ERROR", "SYSTEM"]
CredentialHealth = Literal["healthy", "expired"]


@dataclass
class TaskDefinition:
    id: int
    name: str
    type: str
    type_label: str
    description: str | None
    enabled: bool
    cron: str | None
    payload: dict[str, Any]
    status: str
    latest_run_id: int | None
    latest_run_status: str | None
    latest_run_started_at: datetime | None
    latest_run_finished_at: datetime | None
    latest_error_message: str | None
    metrics_label: str
    metrics_value: str
    timing_label: str
    timing_value: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


CrawlTask = TaskDefinition


@dataclass
class TaskRun:
    id: int
    task_id: int
    task_name: str
    task_type: str
    trigger_mode: str
    status: str
    requested_by: str
    summary: str | None
    metrics_value: str
    error_message: str | None
    termination_reason: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass
class TaskRunLog:
    id: int
    run_id: int
    severity: str
    message: str
    created_at: datetime


@dataclass
class Credential:
    id: int
    name: str
    description: str | None
    raw_key: str
    quota_info: str | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass
class LogRecord:
    id: int
    severity: str
    message: str
    highlighted_terms: list[str] | None
    created_at: datetime
