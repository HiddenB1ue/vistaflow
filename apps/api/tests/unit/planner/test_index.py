from __future__ import annotations

from app.models import StopEvent, Timetable
from app.planner.index import build_station_index


def make_timetable() -> Timetable:
    return {
        "train_001": [
            StopEvent("train_001", 1, "北京南", "G1", None, 480),
            StopEvent("train_001", 2, "济南西", "G1", 600, 610),
            StopEvent("train_001", 3, "上海虹桥", "G1", 750, None),
        ],
        "train_002": [
            StopEvent("train_002", 1, "上海虹桥", "G2", None, 500),
            StopEvent("train_002", 2, "杭州东", "G2", 560, None),
        ],
    }


def test_index_contains_departure_stations() -> None:
    index = build_station_index(make_timetable())
    assert "北京南" in index
    assert "济南西" in index
    assert "上海虹桥" in index  # train_002 在此出发


def test_index_excludes_terminal_arrival() -> None:
    """终到站（无 depart_abs_min）不应被索引为上车点。"""
    index = build_station_index(make_timetable())
    # train_001 的上海虹桥是终到站，depart_abs_min=None，不应出现在 train_001 的索引里
    entries = index.get("上海虹桥", [])
    train_nos = [t for t, _ in entries]
    assert "train_001" not in train_nos
    assert "train_002" in train_nos


def test_index_board_index_correct() -> None:
    index = build_station_index(make_timetable())
    entries = dict(index["北京南"])
    assert entries["train_001"] == 0  # 北京南是第 0 个事件
