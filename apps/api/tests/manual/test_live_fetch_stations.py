from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.integrations.crawler.client import (
    STATION_PATTERN,
    STATION_SOURCE_URL,
    Live12306CrawlerClient,
)
from tests.manual._live_helpers import LIVE_TEST_SKIP_MARK

pytestmark = LIVE_TEST_SKIP_MARK


def _extract_raw_station_rows(source_text: str) -> list[dict[str, str]]:
    match = STATION_PATTERN.search(source_text)
    assert match is not None, "station_names not found in raw 12306 source"

    rows: list[dict[str, str]] = []
    for raw_item in match.group(1).split("@"):
        if not raw_item:
            continue
        parts = raw_item.split("|")
        if len(parts) != 11:
            continue
        rows.append(
            {
                "raw_abbr": parts[0],
                "name": parts[1],
                "telecode": parts[2],
                "pinyin": parts[3],
                "abbr": parts[4],
                "area_code": parts[6],
                "area_name": parts[7],
                "country_code": parts[8] or "cn",
                "country_name": parts[9] or "中国",
            }
        )
    return rows


def _project_station_fields(row: dict[str, Any]) -> dict[str, str]:
    return {
        "name": str(row.get("name") or ""),
        "telecode": str(row.get("telecode") or ""),
        "pinyin": str(row.get("pinyin") or ""),
        "abbr": str(row.get("abbr") or ""),
        "area_code": str(row.get("area_code") or ""),
        "area_name": str(row.get("area_name") or ""),
        "country_code": str(row.get("country_code") or ""),
        "country_name": str(row.get("country_name") or ""),
    }


@pytest.mark.asyncio
async def test_live_fetch_stations_matches_raw_12306_response() -> None:
    async with httpx.AsyncClient() as http_client:
        raw_response = await http_client.get(STATION_SOURCE_URL, timeout=30.0)
        raw_response.raise_for_status()
        raw_text = raw_response.text

        client = Live12306CrawlerClient(http_client=http_client)
        stations = await client.fetch_stations()

    raw_rows = _extract_raw_station_rows(raw_text)
    assert raw_rows, "raw 12306 station rows should not be empty"
    assert stations, "parsed 12306 station rows should not be empty"
    assert len(raw_rows) == len(stations)

    print(f"raw station count = {len(raw_rows)}")
    print(f"parsed station count = {len(stations)}")
    print("raw sample:")
    for item in raw_rows[:3]:
        print(item)
    print("parsed sample:")
    for item in stations[:3]:
        print(item)

    for index, raw_row in enumerate(raw_rows[:10]):
        parsed_row = _project_station_fields(stations[index])
        expected_row = {
            "name": raw_row["name"],
            "telecode": raw_row["telecode"],
            "pinyin": raw_row["pinyin"],
            "abbr": raw_row["abbr"],
            "area_code": raw_row["area_code"],
            "area_name": raw_row["area_name"],
            "country_code": raw_row["country_code"],
            "country_name": raw_row["country_name"],
        }
        assert parsed_row == expected_row
