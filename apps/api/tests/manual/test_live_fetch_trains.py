from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.integrations.crawler.client import Live12306CrawlerClient, seed_keywords
from app.railway.repository import dedupe_train_rows

TEST_DATE = "2026-04-10"
TEST_KEYWORD = "G2"


def normalize_iso_date(raw: str) -> str:
    text = raw.strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    raise ValueError("date must be YYYY-MM-DD or YYYYMMDD")


async def main() -> None:
    date = normalize_iso_date(TEST_DATE)
    cleaned_keyword = TEST_KEYWORD.strip()
    seeds = [cleaned_keyword] if cleaned_keyword else seed_keywords()

    all_rows: list[dict[str, object]] = []
    async with httpx.AsyncClient() as http_client:
        client = Live12306CrawlerClient(http_client=http_client)
        for seed in seeds:
            rows = await client.fetch_trains(date, seed)
            if not rows:
                print(f"[WARN] seed={seed} returned no rows")
                continue

            all_rows.extend(rows)
            seed_unique_rows = dedupe_train_rows(rows)
            print(
                {
                    "seed": seed,
                    "rawRows": len(rows),
                    "uniqueTrainNos": len(seed_unique_rows),
                    "sampleKeywords": sorted(
                        {str(row.get('keyword') or '') for row in rows if row.get("keyword")}
                    )[:20],
                }
            )

    if not all_rows:
        raise RuntimeError("crawler returned no rows")

    deduped_rows = dedupe_train_rows(all_rows)
    print(f"fetch date = {date}")
    print(f"seed keywords = {seeds}")
    print(f"raw rows fetched = {len(all_rows)}")
    print(f"unique train_nos = {len(deduped_rows)}")
    print(f"duplicate rows skipped = {len(all_rows) - len(deduped_rows)}")
    print("row sample:")
    for row in all_rows[:20]:
        print(row)


if __name__ == "__main__":
    asyncio.run(main())
