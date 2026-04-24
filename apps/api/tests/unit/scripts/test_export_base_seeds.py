from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.export_base_seeds import (
    STATIONS_COLUMNS,
    TRAINS_COLUMNS,
    TRAIN_STOPS_COLUMNS,
    _serialize_value,
    write_csv,
)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def test_trains_csv_column_order_matches_seed_sql_contract() -> None:
    assert TRAINS_COLUMNS == (
        "train_no",
        "station_train_code",
        "from_station_id",
        "to_station_id",
        "from_station",
        "to_station",
        "total_num",
        "is_active",
        "created_at",
        "updated_at",
    )


def test_serialize_value_formats_supported_types() -> None:
    assert _serialize_value(None) == ""
    assert _serialize_value(True) == "true"
    assert _serialize_value(False) == "false"
    assert _serialize_value(12) == "12"
    assert _serialize_value("abc") == "abc"


@pytest.mark.parametrize(
    ("filename", "columns", "rows", "expected"),
    [
        (
            "stations.csv",
            STATIONS_COLUMNS,
            [
                {
                    "id": 1,
                    "telecode": "BJP",
                    "name": "北京",
                    "country_name": "中国",
                    "created_at": "2026-04-24 12:00:00+00",
                }
            ],
            [
                {
                    "id": "1",
                    "telecode": "BJP",
                    "name": "北京",
                    "pinyin": "",
                    "abbr": "",
                    "area_code": "",
                    "area_name": "",
                    "country_code": "",
                    "country_name": "中国",
                    "longitude": "",
                    "latitude": "",
                    "geo_source": "",
                    "geo_updated_at": "",
                    "created_at": "2026-04-24 12:00:00+00",
                    "updated_at": "",
                }
            ],
        ),
        (
            "trains.csv",
            TRAINS_COLUMNS,
            [
                {
                    "train_no": "240000G1010A",
                    "station_train_code": "G101",
                    "from_station_id": 1,
                    "to_station_id": 2,
                    "is_active": True,
                }
            ],
            [
                {
                    "train_no": "240000G1010A",
                    "station_train_code": "G101",
                    "from_station_id": "1",
                    "to_station_id": "2",
                    "from_station": "",
                    "to_station": "",
                    "total_num": "",
                    "is_active": "true",
                    "created_at": "",
                    "updated_at": "",
                }
            ],
        ),
        (
            "train_stops.csv",
            TRAIN_STOPS_COLUMNS,
            [
                {
                    "train_no": "240000G1010A",
                    "station_no": 1,
                    "station_name": "北京南",
                    "arrive_day_diff": 0,
                }
            ],
            [
                {
                    "train_no": "240000G1010A",
                    "station_no": "1",
                    "station_name": "北京南",
                    "station_train_code": "",
                    "arrive_time": "",
                    "start_time": "",
                    "running_time": "",
                    "arrive_day_diff": "0",
                    "arrive_day_str": "",
                    "is_start": "",
                    "start_station_name": "",
                    "end_station_name": "",
                    "train_class_name": "",
                    "service_type": "",
                    "wz_num": "",
                    "created_at": "",
                    "updated_at": "",
                }
            ],
        ),
    ],
)
def test_write_csv_writes_expected_headers_and_rows(
    tmp_path: Path,
    filename: str,
    columns: tuple[str, ...],
    rows: list[dict[str, object]],
    expected: list[dict[str, str]],
) -> None:
    output_path = tmp_path / filename

    write_csv(output_path, columns, rows)

    assert _read_csv_rows(output_path) == expected
