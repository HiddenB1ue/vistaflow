from __future__ import annotations


def parse_hhmm(value: str | None) -> int | None:
    """将 'HH:MM' 字符串转换为当天的分钟数，无效值返回 None。"""
    if not value:
        return None
    value = value.strip()
    if ":" not in value:
        return None
    parts = value.split(":")
    if len(parts) != 2:
        return None
    try:
        hours, minutes = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        return None
    return hours * 60 + minutes


def advance_past(value: int, threshold: int, day_minutes: int = 1440) -> int:
    """若 value < threshold，将 value 向前推进整数天直到超过 threshold。"""
    while value < threshold:
        value += day_minutes
    return value


def abs_min_to_hhmm(abs_min: int) -> str:
    """将绝对分钟数转换为 'HH:MM' 字符串（忽略跨天偏移）。"""
    total = abs_min % 1440
    return f"{total // 60:02d}:{total % 60:02d}"


def duration_to_hhmm(minutes: int) -> str:
    """将分钟数格式化为 'Xh Ym' 字符串，如 '4h 35m'。"""
    h, m = divmod(minutes, 60)
    if h == 0:
        return f"{m}m"
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"
