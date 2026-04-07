from __future__ import annotations

import httpx
import pytest

from app.integrations.crawler.client import (
    CRAWL_HEADERS,
    TRAIN_SEARCH_URL,
    Live12306CrawlerClient,
)
from tests.manual._live_helpers import (
    LIVE_TEST_SKIP_MARK,
    normalize_iso_date,
    normalize_search_date,
    normalize_station_name,
    to_int,
)

pytestmark = LIVE_TEST_SKIP_MARK

TEST_DATE = "2026-04-10"
TEST_KEYWORD = "Z"


@pytest.mark.asyncio
async def test_live_fetch_trains_matches_raw_12306_response() -> None:
    date = TEST_DATE
    keyword = TEST_KEYWORD
    compact_date = normalize_search_date(date)
    normalized_date = normalize_iso_date(date)
    cleaned_keyword = keyword.strip()

    async with httpx.AsyncClient() as http_client:
        raw_response = await http_client.get(
            TRAIN_SEARCH_URL,
            params={"keyword": cleaned_keyword, "date": compact_date},
            headers=CRAWL_HEADERS,
            timeout=20.0,
            follow_redirects=False,
        )
        raw_response.raise_for_status()
        raw_payload = raw_response.json()

        client = Live12306CrawlerClient(http_client=http_client)
        parsed_rows = await client.fetch_trains(date, keyword)

    assert isinstance(raw_payload, dict), "raw search response should be a JSON object"
    assert raw_payload.get("status"), f"12306 search failed: {raw_payload}"

    raw_rows = raw_payload.get("data")
    assert isinstance(raw_rows, list), "raw 12306 search data should be a list"

    raw_dict_rows = [row for row in raw_rows if isinstance(row, dict)]

    print(f"search date = {date}")
    print(f"search keyword = {cleaned_keyword}")
    print(f"raw train count = {len(raw_dict_rows)}")
    print(f"parsed train count = {len(parsed_rows)}")
    print("raw sample:")
    for item in raw_dict_rows[:3]:
        print(item)
    print("parsed sample:")
    for item in parsed_rows[:3]:
        print(item)

    assert len(parsed_rows) == len(raw_dict_rows)

    for index, raw_row in enumerate(raw_dict_rows[:10]):
        expected_row = {
            "run_date": normalized_date,
            "date": compact_date,
            "train_no": str(raw_row.get("train_no") or "").strip(),
            "station_train_code": str(raw_row.get("station_train_code") or "").strip(),
            "from_station": normalize_station_name(raw_row.get("from_station")),
            "to_station": normalize_station_name(raw_row.get("to_station")),
            "total_num": to_int(raw_row.get("total_num")),
            "data_flag": raw_row.get("data"),
            "keyword": cleaned_keyword,
        }
        assert parsed_rows[index] == expected_row
