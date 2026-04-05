from __future__ import annotations

from typing import Any

from app.models import SeatInfo

LEFT_TICKET_BASE = "https://kyfw.12306.cn/otn/leftTicket"

DISPLAY_SEATS = ["swz", "tz", "zy", "ze", "gr", "rw", "yw", "yz", "wz", "gg"]

# 12306 响应字段索引
_IDX: dict[str, int] = {
    "train_no": 2,
    "station_train_code": 3,
    "from_station_telecode": 6,
    "to_station_telecode": 7,
    "yp_info_new": 39,
    "gg_num": 20,
    "gr_num": 21,
    "rw_num": 23,
    "tz_num": 25,
    "wz_num": 26,
    "yw_num": 28,
    "yz_num": 29,
    "ze_num": 30,
    "zy_num": 31,
    "swz_num": 32,
}

_SEAT_STATUS_KEYS = {
    "gr": "gr_num", "rw": "rw_num", "tz": "tz_num", "wz": "wz_num",
    "yw": "yw_num", "yz": "yz_num", "ze": "ze_num", "zy": "zy_num",
    "swz": "swz_num", "gg": "gg_num",
}

_SEAT_CODE_TO_NAME: dict[str, str] = {
    "P": "tz", "9": "swz", "D": "gg", "M": "zy", "O": "ze",
    "6": "gr", "I": "rw", "4": "rw", "J": "yw", "3": "yw",
    "1": "yz", "W": "wz",
}

BASE_HEADERS: dict[str, str] = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Origin": "https://kyfw.12306.cn",
    "Referer": "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Cache-Control": "no-cache",
    "If-Modified-Since": "0",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}


def _get_field(parts: list[str], idx: int) -> str:
    return parts[idx] if 0 <= idx < len(parts) else ""


def _to_float(value: Any) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _parse_yp_info_new(raw: str) -> dict[str, float]:
    """解析 yp_info_new 字段，返回 {seat_name: price_yuan}。"""
    price_by_seat: dict[str, float] = {}
    text = (raw or "").strip()
    for i in range(0, len(text), 10):
        chunk = text[i : i + 10]
        if len(chunk) != 10:
            continue
        seat_code = chunk[0]
        price_raw = chunk[1:6]
        if not price_raw.isdigit():
            continue
        seat_name = _SEAT_CODE_TO_NAME.get(seat_code, "").lower()
        if not seat_name:
            continue
        price = int(price_raw) / 10
        if seat_name not in price_by_seat or price < price_by_seat[seat_name]:
            price_by_seat[seat_name] = price
    return price_by_seat


def _is_available(status: str) -> bool:
    text = status.strip()
    if not text or text in {"-", "--", "无", "*", "候补", "列车停运"}:
        return False
    if text == "有":
        return True
    if text.isdigit():
        return int(text) > 0
    if text.endswith("张") and text[:-1].isdigit():
        return int(text[:-1]) > 0
    return False


def parse_result_row(raw: str) -> tuple[str, str, dict[str, str], dict[str, float]]:
    """解析单行 12306 结果，返回 (train_no, station_train_code, seat_status, seat_prices)。"""
    parts = raw.split("|")
    train_no = _get_field(parts, _IDX["train_no"])
    station_train_code = _get_field(parts, _IDX["station_train_code"])
    seat_status = {
        seat: _get_field(parts, _IDX[key])
        for seat, key in _SEAT_STATUS_KEYS.items()
    }
    seat_prices = _parse_yp_info_new(_get_field(parts, _IDX["yp_info_new"]))
    # 无座价格兜底：取最低席别价格
    if "wz" not in seat_prices and seat_prices:
        seat_prices["wz"] = min(seat_prices.values())
    return train_no, station_train_code, seat_status, seat_prices


def build_seat_infos(
    seat_status: dict[str, str],
    seat_prices: dict[str, float],
) -> list[SeatInfo]:
    """从席别状态和价格字典构建 SeatInfo 列表。"""
    seats: list[SeatInfo] = []
    for seat_type in DISPLAY_SEATS:
        status = seat_status.get(seat_type, "").strip()
        price = seat_prices.get(seat_type)
        if price is None and status in {"", "-"}:
            continue
        seats.append(
            SeatInfo(
                seat_type=seat_type,
                status=status or "--",
                price=price,
                available=_is_available(status),
            )
        )
    return seats


def segment_min_price(seats: list[SeatInfo]) -> float | None:
    candidates = [s.price for s in seats if s.available and s.price is not None]
    return min(candidates) if candidates else None
