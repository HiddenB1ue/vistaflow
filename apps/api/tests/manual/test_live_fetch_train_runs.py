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
from app.tasks.handlers import build_train_run_rows, derive_train_rows_from_runs

TEST_DATE = "2026-04-10"
TEST_TRAIN_CODE = "G2"


def normalize_iso_date(raw: str) -> str:
    text = raw.strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    raise ValueError("date must be YYYY-MM-DD or YYYYMMDD")


async def main() -> None:
    date = normalize_iso_date(TEST_DATE)
    train_code = TEST_TRAIN_CODE.strip()
    if not train_code:
        raise ValueError("TEST_TRAIN_CODE cannot be empty")

    async with httpx.AsyncClient() as http_client:
        client = Live12306CrawlerClient(http_client=http_client)
        raw_rows = await client.fetch_train_runs(date, train_code)

    run_rows = build_train_run_rows(raw_rows, run_date=date, train_code=train_code)
    train_rows = derive_train_rows_from_runs(run_rows)

    print(f"fetch date = {date}")
    print(f"train code prefix = {train_code}")
    print(f"raw rows fetched = {len(raw_rows)}")
    print(f"filtered run rows = {len(run_rows)}")
    print(f"derived train rows = {len(train_rows)}")
    print(
        "sample station_train_codes =",
        sorted({str(row.get('station_train_code') or '') for row in run_rows})[:30],
    )
    print("run row sample:")
    for row in run_rows[:20]:
        print(row)


if __name__ == "__main__":
    asyncio.run(main())
