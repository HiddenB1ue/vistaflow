from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Final

import asyncpg

DEFAULT_OUTPUT_DIR: Final[Path] = (
    Path(__file__).resolve().parents[3] / "infra" / "sql" / "seeds"
)

STATIONS_COLUMNS: Final[tuple[str, ...]] = (
    "id",
    "telecode",
    "name",
    "pinyin",
    "abbr",
    "area_code",
    "area_name",
    "country_code",
    "country_name",
    "longitude",
    "latitude",
    "geo_source",
    "geo_updated_at",
    "created_at",
    "updated_at",
)

TRAINS_COLUMNS: Final[tuple[str, ...]] = (
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

TRAIN_STOPS_COLUMNS: Final[tuple[str, ...]] = (
    "train_no",
    "station_no",
    "station_name",
    "station_train_code",
    "arrive_time",
    "start_time",
    "running_time",
    "arrive_day_diff",
    "arrive_day_str",
    "is_start",
    "start_station_name",
    "end_station_name",
    "train_class_name",
    "service_type",
    "wz_num",
    "created_at",
    "updated_at",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export stations, trains and train_stops to CSV seed files.",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", ""),
        help="PostgreSQL DSN. Defaults to DATABASE_URL.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated CSV seed files.",
    )
    return parser


def _serialize_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _serialize_value(row.get(column)) for column in columns})


async def fetch_rows(
    connection: asyncpg.Connection,
    table: str,
    columns: tuple[str, ...],
    order_by: str,
) -> list[dict[str, object]]:
    sql = f"SELECT {', '.join(columns)} FROM {table} ORDER BY {order_by}"
    rows = await connection.fetch(sql)
    return [dict(row) for row in rows]


async def export_seeds(database_url: str, output_dir: Path) -> dict[str, int]:
    if not database_url.strip():
        raise ValueError("database url is required")

    connection = await asyncpg.connect(database_url)
    try:
        stations = await fetch_rows(connection, "stations", STATIONS_COLUMNS, "id")
        trains = await fetch_rows(connection, "trains", TRAINS_COLUMNS, "id")
        train_stops = await fetch_rows(
            connection,
            "train_stops",
            TRAIN_STOPS_COLUMNS,
            "train_no, station_no",
        )
    finally:
        await connection.close()

    write_csv(output_dir / "stations.csv", STATIONS_COLUMNS, stations)
    write_csv(output_dir / "trains.csv", TRAINS_COLUMNS, trains)
    write_csv(output_dir / "train_stops.csv", TRAIN_STOPS_COLUMNS, train_stops)

    return {
        "stations": len(stations),
        "trains": len(trains),
        "train_stops": len(train_stops),
    }


async def _async_main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    summary = await export_seeds(
        database_url=args.database_url,
        output_dir=Path(args.output_dir).resolve(),
    )
    print(
        "Exported seed CSV files: "
        f"stations={summary['stations']}, "
        f"trains={summary['trains']}, "
        f"train_stops={summary['train_stops']}"
    )


def main() -> None:
    import asyncio

    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
