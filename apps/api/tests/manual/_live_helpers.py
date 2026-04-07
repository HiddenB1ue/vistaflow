from __future__ import annotations

import os
from typing import Any

import pytest

RUN_LIVE_TESTS = os.getenv("RUN_LIVE_12306_TESTS") == "1"

LIVE_TEST_SKIP_MARK = pytest.mark.skipif(
    not RUN_LIVE_TESTS,
    reason=(
        "manual live test is disabled by default; "
        "set RUN_LIVE_12306_TESTS=1 to enable"
    ),
)


def normalize_search_date(raw: str) -> str:
    text = raw.strip()
    if len(text) == 8 and text.isdigit():
        return text
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return f"{text[:4]}{text[5:7]}{text[8:10]}"
    raise AssertionError("date must be YYYY-MM-DD or YYYYMMDD")


def normalize_iso_date(raw: str) -> str:
    text = raw.strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    raise AssertionError("date must be YYYY-MM-DD or YYYYMMDD")


def normalize_station_name(value: Any) -> str:
    return "".join(str(value or "").split())


def to_int(value: Any) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None
