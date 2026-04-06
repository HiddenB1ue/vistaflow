from __future__ import annotations

from app.railway.repository import dedupe_train_rows


def test_dedupe_train_rows_keeps_first_row_per_train_no() -> None:
    rows = [
        {"train_no": "240000G1010A", "station_train_code": "G1"},
        {"train_no": "240000G1010A", "station_train_code": "G1-dup"},
        {"train_no": "240000D3010B", "station_train_code": "D301"},
    ]

    result = dedupe_train_rows(rows)

    assert result == [rows[0], rows[2]]
