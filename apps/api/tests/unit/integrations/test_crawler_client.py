from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.integrations.crawler.client import Live12306CrawlerClient


def _make_rows(count: int, *, prefix: str, last_code: str | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(count):
        code = f"{prefix}{index + 1}"
        if last_code is not None and index == count - 1:
            code = last_code
        rows.append(
            {
                "run_date": "2026-04-05",
                "date": "20260405",
                "train_no": f"TN-{code}",
                "station_train_code": code,
                "from_station": "北京南",
                "to_station": "上海虹桥",
                "total_num": 2,
                "data_flag": "1",
                "keyword": prefix,
            }
        )
    return rows


@pytest.mark.asyncio
async def test_fetch_trains_expands_keyword_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Live12306CrawlerClient(http_client=AsyncMock())
    responses = {
        "G": (_make_rows(200, prefix="G", last_code="G1234"), 0),
        **{
            f"G{index}": (_make_rows(1, prefix=f"G{index}"), 0)
            for index in range(1, 10)
        },
    }

    async def fake_fetch(date: str, keyword: str) -> tuple[list[dict[str, str]], int]:
        return responses[keyword]

    monkeypatch.setattr(client, "_fetch_trains_once", fake_fetch)
    monkeypatch.setattr(client, "_sleep_after_request", AsyncMock())

    rows = await client.fetch_trains("2026-04-05", "G")

    assert len(rows) == 209
    assert rows[0]["keyword"] == "G"
    assert any(row["keyword"] == "G1" for row in rows)
    assert any(row["keyword"] == "G9" for row in rows)


@pytest.mark.asyncio
async def test_fetch_trains_recursively_expands_sub_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Live12306CrawlerClient(http_client=AsyncMock())
    responses = {
        "G1": (_make_rows(200, prefix="G1", last_code="G11234"), 0),
        **{
            f"G1{index}": (_make_rows(1, prefix=f"G1{index}"), 0)
            for index in range(10)
        },
    }

    async def fake_fetch(date: str, keyword: str) -> tuple[list[dict[str, str]], int]:
        return responses[keyword]

    monkeypatch.setattr(client, "_fetch_trains_once", fake_fetch)
    monkeypatch.setattr(client, "_sleep_after_request", AsyncMock())

    rows = await client.fetch_trains("2026-04-05", "G1")

    assert len(rows) == 210
    assert rows[0]["keyword"] == "G1"
    assert any(row["keyword"] == "G10" for row in rows)
    assert any(row["keyword"] == "G19" for row in rows)


@pytest.mark.asyncio
async def test_fetch_trains_dedupes_by_station_train_code(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Live12306CrawlerClient(http_client=AsyncMock())
    duplicate_row = {
        "run_date": "2026-04-05",
        "date": "20260405",
        "train_no": "TN-DUP",
        "station_train_code": "G1",
        "from_station": "北京南",
        "to_station": "上海虹桥",
        "total_num": 2,
        "data_flag": "1",
        "keyword": "G",
    }
    responses = {
        "G": ([duplicate_row | {"keyword": "G"}] * 200, 0),
        **{
            f"G{index}": ([duplicate_row | {"keyword": f"G{index}"}], 0)
            for index in range(1, 10)
        },
    }

    async def fake_fetch(date: str, keyword: str) -> tuple[list[dict[str, str]], int]:
        return responses[keyword]

    monkeypatch.setattr(client, "_fetch_trains_once", fake_fetch)
    monkeypatch.setattr(client, "_sleep_after_request", AsyncMock())

    rows = await client.fetch_trains("2026-04-05", "G")

    assert len(rows) == 1
    assert rows[0]["station_train_code"] == "G1"
