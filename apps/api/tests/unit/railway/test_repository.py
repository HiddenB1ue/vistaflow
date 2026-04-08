from __future__ import annotations

from datetime import date as date_type

from app.railway.repository import _to_date, dedupe_train_rows


def test_dedupe_train_rows_keeps_first_row_per_train_no() -> None:
    rows = [
        {"train_no": "240000G1010A", "station_train_code": "G1"},
        {"train_no": "240000G1010A", "station_train_code": "G1-dup"},
        {"train_no": "240000D3010B", "station_train_code": "D301"},
    ]

    result = dedupe_train_rows(rows)

    assert result == [rows[0], rows[2]]


def test_to_date_normalizes_iso_string() -> None:
    assert _to_date("2026-04-10") == date_type(2026, 4, 10)


def test_to_date_normalizes_compact_string() -> None:
    assert _to_date("20260410") == date_type(2026, 4, 10)


def test_to_date_preserves_date_object() -> None:
    value = date_type(2026, 4, 10)

    assert _to_date(value) == value
