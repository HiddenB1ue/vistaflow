from __future__ import annotations

from app.integrations.ticket_12306.parser import (
    build_seat_infos,
    parse_result_row,
    segment_min_price,
)
from app.models import SeatInfo


def _build_result_row(**fields: str) -> str:
    parts = [""] * 40
    index_map = {
        "train_no": 2,
        "station_train_code": 3,
        "from_station_telecode": 6,
        "to_station_telecode": 7,
        "gg_num": 20,
        "gr_num": 21,
        "rw_num": 23,
        "tz_num": 25,
        "wz_num": 26,
        "yw_num": 28,
        "yz_num": 29,
        "ze_num": 30,
        "zy_num": 31,
        "swz_num": 32,
        "yp_info_new": 39,
    }
    for key, value in fields.items():
        parts[index_map[key]] = value
    return "|".join(parts)


def test_parse_result_row_does_not_fabricate_wz_price() -> None:
    row = _build_result_row(
        train_no="240000G1010A",
        station_train_code="G101",
        wz_num="有",
        ze_num="5",
        zy_num="无",
        yp_info_new="M032000000O019000000",
    )

    train_no, station_train_code, seat_status, seat_prices = parse_result_row(row)

    assert train_no == "240000G1010A"
    assert station_train_code == "G101"
    assert seat_status["wz"] == "有"
    assert seat_prices == {"zy": 320.0, "ze": 190.0}
    assert "wz" not in seat_prices


def test_build_seat_infos_keeps_available_wz_without_price() -> None:
    seats = build_seat_infos({"wz": "有"}, {})

    assert seats == [
        SeatInfo(
            seat_type="wz",
            status="有",
            price=None,
            available=True,
        )
    ]


def test_build_seat_infos_skips_empty_seat_without_price() -> None:
    seats = build_seat_infos({"wz": "-"}, {})

    assert seats == []


def test_segment_min_price_ignores_null_prices() -> None:
    assert segment_min_price(
        [SeatInfo(seat_type="wz", status="有", price=None, available=True)]
    ) is None

    assert segment_min_price(
        [
            SeatInfo(seat_type="wz", status="有", price=None, available=True),
            SeatInfo(seat_type="ze", status="有", price=553.0, available=True),
        ]
    ) == 553.0
