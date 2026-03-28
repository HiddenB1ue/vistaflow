from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models import SeatInfo, Segment, StopEvent

# 车次号 → 经停事件列表
Timetable = dict[str, list["StopEvent"]]

# 站名 → [(车次号, 在该车次中的索引)]
StationIndex = dict[str, list[tuple[str, int]]]

# (train_no, from_station, to_station) → 席别列表
SeatLookupKey = tuple[str, str, str]
