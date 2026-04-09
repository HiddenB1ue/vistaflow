from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

# 基础请求头，保持与浏览器访问行为接近。
BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Origin": "https://kyfw.12306.cn",
    "Referer": "https://kyfw.12306.cn/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

LEFT_TICKET_QUERY_URL = "https://kyfw.12306.cn/otn/leftTicket/queryG"
DEFAULT_COOKIE = (
    "_uab_collina=177028072603985136749915; "
    "JSESSIONID=AC542969CC756F45F348F632EC5B4B88; "
    "_jc_save_wfdc_flag=dc; "
    "guidesStatus=off; "
    "highContrastMode=defaltMode; "
    "cursorStatus=off; "
    "_big_fontsize=0; "
    "_c_WBKFRo=Fanm4dlvMc1wbaRhv8bXa85tXv7zd2qPkxLtVscr; "
    "_jc_save_fromStation=%u957F%u6625%2CCCT; "
    "_jc_save_toStation=%u4E0A%u6D77%2CSHH; "
    "_jc_save_fromDate=2026-03-05; "
    "BIGipServerotn=1406730506.64545.0000; "
    "BIGipServerpassport=786956554.50215.0000; "
    "route=c5c62a339e7744272a54643b3be5bf64; "
    "_jc_save_toDate=2026-03-05"
)

# result 串中常用索引。
IDX = {
    "train_no": 2,
    "station_train_code": 3,
    "from_station_telecode": 6,
    "to_station_telecode": 7,
    "start_time": 8,
    "arrive_time": 9,
    "duration": 10,
    "can_web_buy": 11,
    "start_train_date": 13,
    "yp_info_new": 39,
    # 显式余票槽位
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

SEAT_CODE_NAME = {
    "P": "tz",  # 特等座
    "9": "swz",  # 商务座
    "D": "gg",  # 优选一等座
    "M": "zy",  # 一等座
    "O": "ze",  # 二等座
    "6": "gr",  # 高级软卧
    "I": "rw",  # 一等卧
    "4": "rw",  # 软卧
    "J": "yw",  # 二等卧
    "3": "yw",  # 硬卧
    "1": "yz",  # 硬座
    "W": "wz",  # 无座
}

DISPLAY_SEATS = ["swz", "tz", "zy", "ze", "gr", "rw", "yw", "yz", "wz", "gg"]


@dataclass
class TicketRow:
    train_no: str
    station_train_code: str
    from_station_telecode: str
    to_station_telecode: str
    start_time: str
    arrive_time: str
    duration: str
    can_web_buy: str
    start_train_date: str
    yp_info_new: str
    seat_status: dict[str, str]
    seat_prices: list[dict[str, str]]


def _get(parts: list[str], idx: int) -> str:
    if idx < 0 or idx >= len(parts):
        return ""
    return parts[idx]


def parse_yp_info_new(raw: str) -> list[dict[str, str]]:
    """按 10 位一组解析 yp_info_new：1位席别 + 5位价格(角) + 4位附加码。"""
    text = (raw or "").strip()
    if not text:
        return []

    entries: list[dict[str, str]] = []
    for i in range(0, len(text), 10):
        chunk = text[i : i + 10]
        if len(chunk) != 10:
            continue
        seat_code = chunk[0]
        price_raw = chunk[1:6]
        ext_raw = chunk[6:10]
        if not price_raw.isdigit():
            continue
        price_yuan = f"{int(price_raw) / 10:.1f}"
        entries.append(
            {
                "seat_code": seat_code,
                "seat": SEAT_CODE_NAME.get(seat_code, seat_code),
                "price": price_yuan,
                "ext": ext_raw,
                "raw": chunk,
            }
        )
    return entries


def parse_result_row(row: str) -> TicketRow:
    parts = row.split("|")
    seat_status = {
        "gr": _get(parts, IDX["gr_num"]),
        "rw": _get(parts, IDX["rw_num"]),
        "tz": _get(parts, IDX["tz_num"]),
        "wz": _get(parts, IDX["wz_num"]),
        "yw": _get(parts, IDX["yw_num"]),
        "yz": _get(parts, IDX["yz_num"]),
        "ze": _get(parts, IDX["ze_num"]),
        "zy": _get(parts, IDX["zy_num"]),
        "swz": _get(parts, IDX["swz_num"]),
        "gg": _get(parts, IDX["gg_num"]),
    }

    yp_info_new = _get(parts, IDX["yp_info_new"])
    return TicketRow(
        train_no=_get(parts, IDX["train_no"]),
        station_train_code=_get(parts, IDX["station_train_code"]),
        from_station_telecode=_get(parts, IDX["from_station_telecode"]),
        to_station_telecode=_get(parts, IDX["to_station_telecode"]),
        start_time=_get(parts, IDX["start_time"]),
        arrive_time=_get(parts, IDX["arrive_time"]),
        duration=_get(parts, IDX["duration"]),
        can_web_buy=_get(parts, IDX["can_web_buy"]),
        start_train_date=_get(parts, IDX["start_train_date"]),
        yp_info_new=yp_info_new,
        seat_status=seat_status,
        seat_prices=parse_yp_info_new(yp_info_new),
    )


def fetch_left_ticket_payload(
    train_date: str,
    from_station: str,
    to_station: str,
    cookie: str,
) -> dict[str, Any]:
    params = {
        "leftTicketDTO.train_date": train_date,
        "leftTicketDTO.from_station": from_station,
        "leftTicketDTO.to_station": to_station,
        "purpose_codes": "ADULT",
    }

    headers = dict(BASE_HEADERS)
    headers.update(
        {
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "If-Modified-Since": "0",
            "Origin": "https://kyfw.12306.cn",
            "Referer": "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
        }
    )
    if cookie.strip():
        headers["Cookie"] = cookie.strip()

    with httpx.Client(follow_redirects=False, timeout=20) as client:
        resp = client.get(LEFT_TICKET_QUERY_URL, params=params, headers=headers)

    if resp.status_code == 302:
        raise RuntimeError(
            "got 302 redirect (likely blocked by 12306). "
            "Please pass a fresh browser Cookie via --cookie."
        )
    resp.raise_for_status()

    payload: dict[str, Any] = resp.json()
    if not payload.get("status"):
        raise RuntimeError(f"12306 status=false, messages={payload.get('messages')!r}")
    return payload


def print_rows(rows: list[TicketRow], telecode_map: dict[str, str]) -> None:
    if not rows:
        print("no trains returned.")
        return

    print(f"trains: {len(rows)}")
    for idx, row in enumerate(rows, start=1):
        from_name = telecode_map.get(row.from_station_telecode, row.from_station_telecode)
        to_name = telecode_map.get(row.to_station_telecode, row.to_station_telecode)
        print(
            f"[{idx}] {row.station_train_code}/{row.train_no} "
            f"{from_name}({row.from_station_telecode}) -> {to_name}({row.to_station_telecode}) "
            f"{row.start_time}->{row.arrive_time} duration={row.duration} web_buy={row.can_web_buy}"
        )

        seat_text = ", ".join(
            f"{seat}={row.seat_status.get(seat, '') or '-'}" for seat in DISPLAY_SEATS
        )
        print(f"  seats: {seat_text}")

        if row.seat_prices:
            price_text = "; ".join(
                f"{item['seat']}({item['seat_code']})={item['price']} ext={item['ext']}"
                for item in row.seat_prices
            )
            print(f"  yp_info_new: {price_text}")
        else:
            print("  yp_info_new: (empty)")


def main() -> None:
    # ===== 手动修改区（按需改这里）=====
    train_date = "2026-03-06"
    from_station = "JXH"  # 例如 CCT=长春
    to_station = "IMH"  # 例如 SHH=上海
    cookie = DEFAULT_COOKIE  # 建议粘贴浏览器 Cookie，避免 302
    limit = 0  # 仅打印前 N 条；<=0 表示全打印
    # ==================================

    payload = fetch_left_ticket_payload(
        train_date=train_date,
        from_station=from_station,
        to_station=to_station,
        cookie=cookie,
    )

    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    raw_results = data.get("result") if isinstance(data.get("result"), list) else []
    telecode_map = data.get("map") if isinstance(data.get("map"), dict) else {}

    rows: list[TicketRow] = []
    for raw in raw_results:
        if not isinstance(raw, str):
            continue
        rows.append(parse_result_row(raw))

    if limit > 0:
        rows = rows[:limit]

    print(
        f"httpstatus={payload.get('httpstatus')} status={payload.get('status')} "
        f"from={from_station} to={to_station} date={train_date}"
    )
    print_rows(rows, telecode_map)


if __name__ == "__main__":
    main()
