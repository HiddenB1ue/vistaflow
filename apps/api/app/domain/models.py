from __future__ import annotations

from dataclasses import dataclass


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
