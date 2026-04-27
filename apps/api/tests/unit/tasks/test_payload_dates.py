from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.tasks.payloads import FetchTrainRunsPayload


def test_fixed_date_payload_keeps_legacy_date_format() -> None:
    payload = FetchTrainRunsPayload.model_validate({"date": "20260405", "keyword": " G "})

    assert payload.date_mode == "fixed"
    assert payload.date == "2026-04-05"
    assert payload.keyword == "G"
    assert payload.resolved_date() == "2026-04-05"


def test_relative_date_payload_resolves_against_beijing_date() -> None:
    payload = FetchTrainRunsPayload.model_validate(
        {"dateMode": "relative", "dateOffsetDays": 9}
    )
    now = datetime(2026, 4, 27, 23, 30, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert payload.date is None
    assert payload.date_offset_days == 9
    assert payload.resolved_date(now=now) == "2026-05-06"


def test_relative_date_payload_rejects_out_of_range_offset() -> None:
    with pytest.raises(ValueError):
        FetchTrainRunsPayload.model_validate(
            {"dateMode": "relative", "dateOffsetDays": 61}
        )


def test_fixed_date_payload_requires_date() -> None:
    with pytest.raises(ValueError):
        FetchTrainRunsPayload.model_validate({"dateMode": "fixed"})
