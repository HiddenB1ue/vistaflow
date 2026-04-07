from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import httpx

SOURCE_URL = "https://www.12306.cn/index/script/core/common/station_name_new_v10107.js"
STATION_PATTERN = re.compile(r"var\s+station_names\s*=\s*'(.*?)';", re.S)


def load_js_text(source_url: str, input_file: Path | None) -> str:
    if input_file is not None:
        return input_file.read_text(encoding="utf-8")

    response = httpx.get(source_url, timeout=20)
    response.raise_for_status()
    return response.text


def extract_station_payload(js_text: str) -> str:
    match = STATION_PATTERN.search(js_text)
    if not match:
        raise ValueError("Cannot find `station_names` in input text")
    return match.group(1)


def parse_station_payload(payload: str) -> list[dict[str, Any]]:
    stations: list[dict[str, Any]] = []
    for raw_item in payload.split("@"):
        if not raw_item:
            continue

        parts = raw_item.split("|")
        if len(parts) != 11:
            # Skip malformed rows to keep parser robust when source format changes.
            continue

        stations.append(
            {
                "code": parts[0],
                "name": parts[1],
                "telecode": parts[2],
                "pinyin": parts[3],
                "abbr": parts[4],
                "order": int(parts[5]) if parts[5].isdigit() else None,
                "area_code": parts[6],
                "area_name": parts[7],
                "country_code": parts[8] or None,
                "country_name": parts[9] or None,
                "extra": parts[10] or None,
            }
        )
    return stations


def build_useful_rows(stations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    useful_rows: list[dict[str, Any]] = []
    for station in stations:
        useful_rows.append(
            {
                "name": station["name"],
                "telecode": station["telecode"],
                "pinyin": station["pinyin"],
                "abbr": station["abbr"],
                "area_name": station["area_name"],
                "area_code": station["area_code"],
                "country_name": station["country_name"] or "中国",
                "country_code": station["country_code"] or "cn",
            }
        )
    return useful_rows


def dump_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "telecode",
        "pinyin",
        "abbr",
        "area_name",
        "area_code",
        "country_name",
        "country_code",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def crawl_station(source_url: str, input_file: Path | None, csv_path: Path) -> None:
    js_text = load_js_text(source_url=source_url, input_file=input_file)
    payload = extract_station_payload(js_text)
    stations = parse_station_payload(payload)
    useful_rows = build_useful_rows(stations)

    dump_csv(useful_rows, csv_path)

    print(f"Parsed stations: {len(stations)}")
    print(f"CSV output: {csv_path}")
    print("Sample rows:")
    for row in useful_rows[:5]:
        print(row)


def main() -> None:
    # ===== 手动修改区（按需改这里）=====
    source_url = SOURCE_URL
    input_file: Path | None = None  # 例如 Path("test/output/station_name_new.js")
    csv_output = Path("test/output/stations_v1.csv")
    # ==================================

    crawl_station(
        source_url=source_url,
        input_file=input_file,
        csv_path=csv_output,
    )


if __name__ == "__main__":
    main()
