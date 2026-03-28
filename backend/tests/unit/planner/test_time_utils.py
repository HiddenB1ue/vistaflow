from __future__ import annotations

import pytest

from app.domain.models import StopEvent
from app.domain.types import Timetable
from app.planner.time_utils import abs_min_to_hhmm, advance_past, duration_to_hhmm, parse_hhmm


# --- parse_hhmm ---

def test_parse_hhmm_valid() -> None:
    assert parse_hhmm("08:00") == 480
    assert parse_hhmm("00:00") == 0
    assert parse_hhmm("23:59") == 1439


def test_parse_hhmm_invalid() -> None:
    assert parse_hhmm(None) is None
    assert parse_hhmm("") is None
    assert parse_hhmm("abc") is None
    assert parse_hhmm("25:00") is None
    assert parse_hhmm("08:60") is None


# --- advance_past ---

def test_advance_past_no_advance_needed() -> None:
    assert advance_past(600, 480) == 600


def test_advance_past_single_day() -> None:
    assert advance_past(300, 480) == 300 + 1440


# --- abs_min_to_hhmm ---

def test_abs_min_to_hhmm() -> None:
    assert abs_min_to_hhmm(480) == "08:00"
    assert abs_min_to_hhmm(1439) == "23:59"
    assert abs_min_to_hhmm(1440 + 60) == "01:00"  # 跨天


# --- duration_to_hhmm ---

def test_duration_to_hhmm() -> None:
    assert duration_to_hhmm(275) == "4h 35m"
    assert duration_to_hhmm(60) == "1h"
    assert duration_to_hhmm(45) == "45m"
