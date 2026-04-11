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
    total_stops: int | None = None  # 该车次的全程经停数量


@dataclass(frozen=True)
class Segment:
    """行程中的一段单趟列车。"""

    train_no: str
    train_code: str
    from_station: str
    to_station: str
    depart_abs_min: int
    arrive_abs_min: int
    total_stops: int | None = None  # 该车次的全程经停数量


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
    "fetch-station-geo",
    "fetch-trains",
    "fetch-train-stops",
    "fetch-train-runs",
    "price",
]
TaskStatus = Literal["idle", "pending", "running", "completed", "error", "terminated"]
TaskRunStatus = Literal["pending", "running", "completed", "error", "terminated"]
TaskResultLevel = Literal["success", "warning", "error"]
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
    latest_result_level: str | None
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
    result_level: str | None
    metrics_value: str
    progress_snapshot: dict[str, Any] | None
    error_message: str | None
    termination_reason: str | None
    worker_id: str | None
    heartbeat_at: datetime | None
    cancel_requested: bool
    cancel_requested_at: datetime | None
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


@dataclass
class SystemSetting:
    id: int
    key: str
    value: str
    value_type: str
    category: str
    label: str
    description: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime
