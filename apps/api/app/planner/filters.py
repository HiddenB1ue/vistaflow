from __future__ import annotations

from app.models import Segment, StationIndex, Timetable

MINUTES_PER_DAY = 1440


def get_train_type(train_code: str) -> str:
    """从车次代码中提取车型前缀，如 'G101' → 'G'。"""
    code = train_code.strip().upper()
    if not code:
        return ""
    # 取开头连续的字母部分
    prefix = ""
    for ch in code:
        if ch.isalpha():
            prefix += ch
        else:
            break
    return prefix


def is_train_type_allowed(
    train_code: str,
    allowed_prefixes: tuple[str, ...],
) -> bool:
    """检查车次是否属于允许的车型。allowed_prefixes 为空表示全部允许。"""
    if not allowed_prefixes:
        return True
    train_type = get_train_type(train_code)
    return any(train_type == p.upper() for p in allowed_prefixes)


def is_train_type_excluded(
    train_code: str,
    excluded_prefixes: set[str],
) -> bool:
    """检查车次是否属于排除的车型。"""
    if not excluded_prefixes:
        return False
    return get_train_type(train_code) in {p.upper() for p in excluded_prefixes}


def is_train_token_excluded(
    train_no: str,
    train_code: str,
    excluded_tokens: set[str],
) -> bool:
    """检查车次是否在明确排除的车次列表中（按 train_no 或 train_code 匹配）。"""
    if not excluded_tokens:
        return False
    tokens = {t.upper() for t in excluded_tokens}
    return train_no.upper() in tokens or train_code.upper() in tokens


def is_departure_time_allowed(
    depart_abs_min: int,
    start_min: int | None,
    end_min: int | None,
    cross_day: bool,
) -> bool:
    """检查出发时间是否在允许的时间窗口内。

    cross_day=True 表示窗口跨越午夜（如 22:00 → 06:00）。
    """
    if start_min is None and end_min is None:
        return True

    depart_clock = depart_abs_min % MINUTES_PER_DAY

    if start_min is not None and end_min is not None:
        if cross_day:
            return depart_clock >= start_min or depart_clock <= end_min
        return start_min <= depart_clock <= end_min

    if start_min is not None:
        return depart_clock >= start_min
    return depart_clock <= (end_min or 0)


def get_boardable_trains(
    station: str,
    earliest_depart: int,
    latest_depart: int | None,
    exclude_train_no: str | None,
    allowed_type_prefixes: tuple[str, ...],
    excluded_type_prefixes: set[str],
    excluded_tokens: set[str],
    timetable: Timetable,
    station_index: StationIndex,
) -> list[tuple[str, int, int]]:
    """返回在指定站点可乘坐的列车列表，每项为 (train_no, board_index, depart_abs_min)。

    结果按出发时间升序排列。
    """
    boardable: list[tuple[str, int, int]] = []

    for train_no, board_index in station_index.get(station, []):
        if exclude_train_no and train_no == exclude_train_no:
            continue

        event = timetable[train_no][board_index]
        depart_abs = event.depart_abs_min
        if depart_abs is None:
            continue
        if depart_abs < earliest_depart:
            continue
        if latest_depart is not None and depart_abs > latest_depart:
            continue

        train_code = event.train_code
        if not is_train_type_allowed(train_code, allowed_type_prefixes):
            continue
        if is_train_type_excluded(train_code, excluded_type_prefixes):
            continue
        if is_train_token_excluded(train_no, train_code, excluded_tokens):
            continue

        boardable.append((train_no, board_index, depart_abs))

    boardable.sort(key=lambda item: item[2])
    return boardable


def route_matches_allowed_trains(
    route: list[Segment],
    allowed_tokens: set[str],
) -> bool:
    """若 allowed_tokens 非空，路线中至少有一段使用了允许的车次。"""
    if not allowed_tokens:
        return True
    tokens = {t.upper() for t in allowed_tokens}
    return any(
        segment.train_no.upper() in tokens or segment.train_code.upper() in tokens
        for segment in route
    )


def route_matches_allowed_transfer_stations(
    route: list[Segment],
    allowed_stations: set[str],
) -> bool:
    """若 allowed_stations 非空，换乘站必须在允许列表中。"""
    if not allowed_stations or len(route) <= 1:
        return not allowed_stations or len(route) <= 1
    transfer_stations = {seg.to_station for seg in route[:-1]}
    return not transfer_stations.isdisjoint(allowed_stations)
