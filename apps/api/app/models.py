from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class StopEvent:
    """时刻表中的单个经停事件。"""

    train_no: str
    stop_number: int
    station_name: str
    train_code: str  # 如 "G1"（station_train_code）
    arrive_abs_min: int | None  # 到站绝对分钟数（跨天累加）
    depart_abs_min: int | None  # 出站绝对分钟数


@dataclass(frozen=True)
class Segment:
    """行程中的一段（单趟列车）。"""

    train_no: str
    train_code: str
    from_station: str
    to_station: str
    depart_abs_min: int
    arrive_abs_min: int


@dataclass(frozen=True)
class SeatInfo:
    """席别余票信息。"""

    seat_type: str  # "zy"（一等座）/ "ze"（二等座）等
    status: str  # 显示用状态文字
    price: float | None
    available: bool


# 车次号 → 经停事件列表
Timetable = dict[str, list["StopEvent"]]

# 站名 → [(车次号, 在该车次中的索引)]
StationIndex = dict[str, list[tuple[str, int]]]

# (train_no, from_station, to_station) → 席别列表
SeatLookupKey = tuple[str, str, str]


# ---------------------------------------------------------------------------
# 任务/凭证/日志 类型别名
# ---------------------------------------------------------------------------

TaskType = Literal["fetch-station", "geocode", "fetch-status", "price", "cleanup"]
TaskStatus = Literal["running", "pending", "completed", "error", "terminated"]
LogSeverity = Literal["SUCCESS", "INFO", "WARN", "ERROR", "SYSTEM"]
CredentialHealth = Literal["healthy", "expired"]


# ---------------------------------------------------------------------------
# 任务/凭证/日志 领域模型
# ---------------------------------------------------------------------------


@dataclass
class CrawlTask:
    id: int
    name: str
    type: str
    type_label: str
    status: str
    description: str | None
    cron: str | None
    metrics_label: str
    metrics_value: str
    timing_label: str
    timing_value: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


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
