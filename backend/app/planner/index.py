from __future__ import annotations

from app.domain.models import StopEvent
from app.domain.types import StationIndex, Timetable


def build_station_index(timetable: Timetable) -> StationIndex:
    """构建站名 → [(车次号, 在该车次时刻表中的索引)] 的反向索引。

    只索引有出发时间的经停事件（depart_abs_min is not None），
    因为只有能出发的站才能作为上车点。
    """
    index: StationIndex = {}
    for train_no, events in timetable.items():
        for i, event in enumerate(events):
            if event.depart_abs_min is not None:
                index.setdefault(event.station_name, []).append((train_no, i))
    return index
