# ruff: noqa: E402

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.integrations.crawler.client import Live12306CrawlerClient

TEST_DATE = "2026-04-10"
TEST_TRAIN_NO = "5l0000G20100"


def normalize_iso_date(raw: str) -> str:
    text = raw.strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    raise ValueError("date must be YYYY-MM-DD or YYYYMMDD")


async def main() -> None:
    date = normalize_iso_date(TEST_DATE)
    train_no = TEST_TRAIN_NO.strip()
    if not train_no:
        raise ValueError("TEST_TRAIN_NO cannot be empty")

    async with httpx.AsyncClient() as http_client:
        client = Live12306CrawlerClient(http_client=http_client)
        stop_rows = await client.fetch_train_stops(train_no, date)

    print(f"fetch date = {date}")
    print(f"train_no = {train_no}")
    print(f"stop rows fetched = {len(stop_rows)}")

    if not stop_rows:
        print("[WARN] no stop rows returned")
        return

    station_train_codes = sorted(
        {
            str(row.get("station_train_code") or "")
            for row in stop_rows
            if row.get("station_train_code")
        }
    )
    station_names = [str(row.get("station_name") or "") for row in stop_rows]

    print("station_train_codes =", station_train_codes)
    print(
        "route sample =",
        {
            "first": station_names[0] if station_names else None,
            "last": station_names[-1] if station_names else None,
        },
    )
    print("row sample:")
    for row in stop_rows[:20]:
        print(row)


if __name__ == "__main__":
    asyncio.run(main())
