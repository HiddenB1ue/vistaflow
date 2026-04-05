from __future__ import annotations

from dataclasses import dataclass

from app.models import SeatInfo


@dataclass(frozen=True)
class TicketSegmentData:
    seats: list[SeatInfo]
    min_price: float | None
    matched_by: str  # "train_no" | "station_train_code" | ""


@dataclass(frozen=True)
class TicketLeg:
    """一条查询区间（from_station → to_station），对应 12306 一次接口调用。"""
    from_station: str
    to_station: str
    from_telecode: str
    to_telecode: str
