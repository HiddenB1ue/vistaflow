from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import asyncpg

from app.integrations.crawler.client import AbstractCrawlerClient
from app.integrations.geo.client import AbstractGeoClient
from app.models import TaskDefinition
from app.railway.repository import RailwayTaskRepository, StationRepository
from app.system.log_repository import LogRepository
from app.tasks.exceptions import TaskExecutionError
from app.tasks.repository import TaskRunLogRepository
from app.tasks.schemas import (
    FetchTrainRunsPayload,
    FetchTrainsPayload,
    FetchTrainStopsPayload,
)

GEO_SOURCE_AMAP = "amap_v3_geocode"


@dataclass(frozen=True)
class TaskExecutionResult:
    summary: str
    metrics_value: str = ""
    timing_value: str = ""


@dataclass
class HandlerContext:
    task: TaskDefinition
    run_id: int
    pool: asyncpg.Pool
    run_log_repo: TaskRunLogRepository
    log_repo: LogRepository
    crawler_client: AbstractCrawlerClient
    geo_client: AbstractGeoClient

    async def log(self, severity: str, message: str) -> None:
        await self.run_log_repo.create_log(self.run_id, severity, message)
        await self.log_repo.write_log(
            severity,
            message,
            highlighted_terms=[self.task.type],
        )


async def handle_fetch_station(ctx: HandlerContext) -> TaskExecutionResult:
    await ctx.log("INFO", f"任务 {ctx.task.name} 开始抓取全国车站基础数据")
    stations = await ctx.crawler_client.fetch_stations()
    station_repo = StationRepository(ctx.pool)
    count = await station_repo.upsert_stations(stations)
    await ctx.log("SUCCESS", f"fetch-station 完成，写入 {count} 条记录")
    return TaskExecutionResult(summary="站点基础数据同步完成", metrics_value=str(count))


async def handle_geocode(ctx: HandlerContext) -> TaskExecutionResult:
    await ctx.log("INFO", f"任务 {ctx.task.name} 开始补全站点坐标")
    station_repo = StationRepository(ctx.pool)
    rows = await station_repo.find_missing_geo()
    success_count = 0
    for row in rows:
        result = await ctx.geo_client.geocode_station(
            str(row["name"]),
            str(row.get("area_name") or ""),
        )
        if result is None:
            continue
        longitude, latitude = result
        station_id = row.get("id")
        if not isinstance(station_id, (int, str)):
            continue
        await station_repo.update_geo(
            int(station_id),
            longitude,
            latitude,
            GEO_SOURCE_AMAP,
        )
        success_count += 1
    await ctx.log("SUCCESS", f"geocode 完成，成功补全 {success_count} 个站点")
    return TaskExecutionResult(summary="站点坐标补全完成", metrics_value=str(success_count))


async def handle_fetch_trains(ctx: HandlerContext) -> TaskExecutionResult:
    payload = FetchTrainsPayload.model_validate(ctx.task.payload)
    await ctx.log(
        "INFO",
        f"任务 {ctx.task.name} 开始抓取车次：date={payload.date}, keyword={payload.keyword}",
    )
    rows = await ctx.crawler_client.fetch_trains(payload.date, payload.keyword)
    repo = RailwayTaskRepository(ctx.pool)
    imported = await repo.upsert_train_rows(rows)
    if imported == 0:
        await ctx.log(
            "INFO",
            f"fetch-trains 完成，但未找到匹配车次：keyword={payload.keyword}",
        )
        return TaskExecutionResult(summary="车次同步完成，未找到匹配数据", metrics_value="0")

    await ctx.log("SUCCESS", f"fetch-trains 完成，写入 {imported} 条车次记录")
    return TaskExecutionResult(summary="车次同步完成", metrics_value=str(imported))


async def handle_fetch_train_stops(ctx: HandlerContext) -> TaskExecutionResult:
    payload = FetchTrainStopsPayload.model_validate(ctx.task.payload)
    await ctx.log(
        "INFO",
        f"任务 {ctx.task.name} 开始抓取经停：date={payload.date}, train_code={payload.train_code}",
    )
    train_candidates = await ctx.crawler_client.fetch_trains(payload.date, payload.train_code)
    train_row = resolve_train_row(
        train_candidates,
        run_date=payload.date,
        train_code=payload.train_code,
    )
    stop_rows = await ctx.crawler_client.fetch_train_stops(
        str(train_row["train_no"]),
        payload.date,
    )
    if not stop_rows:
        raise TaskExecutionError(
            f"未找到车次 {payload.train_code} 在 {payload.date} 的经停数据"
        )

    train_rows = derive_train_rows_from_stops(stop_rows)
    repo = RailwayTaskRepository(ctx.pool)
    train_count, stop_count = await repo.upsert_train_and_stop_rows(train_rows, stop_rows)
    await ctx.log(
        "SUCCESS",
        (
            "fetch-train-stops 完成，"
            f"写入 {train_count} 条车次记录和 {stop_count} 条经停记录"
        ),
    )
    return TaskExecutionResult(summary="车次经停同步完成", metrics_value=str(stop_count))


async def handle_fetch_train_runs(ctx: HandlerContext) -> TaskExecutionResult:
    payload = FetchTrainRunsPayload.model_validate(ctx.task.payload)
    await ctx.log(
        "INFO",
        (
            f"任务 {ctx.task.name} 开始抓取运行车次："
            f"date={payload.date}, train_code={payload.train_code}"
        ),
    )
    raw_rows = await ctx.crawler_client.fetch_train_runs(payload.date, payload.train_code)
    run_rows = build_train_run_rows(
        raw_rows,
        run_date=payload.date,
        train_code=payload.train_code,
    )
    if not run_rows:
        raise TaskExecutionError(
            f"未找到车次 {payload.train_code} 在 {payload.date} 的运行事实"
        )

    train_rows = derive_train_rows_from_runs(run_rows)
    repo = RailwayTaskRepository(ctx.pool)
    train_count, run_count = await repo.upsert_train_and_run_rows(train_rows, run_rows)
    await ctx.log(
        "SUCCESS",
        (
            "fetch-train-runs 完成，"
            f"写入 {train_count} 条车次记录和 {run_count} 条运行记录"
        ),
    )
    return TaskExecutionResult(summary="运行车次同步完成", metrics_value=str(run_count))


def resolve_train_row(
    rows: list[dict[str, Any]],
    *,
    run_date: str,
    train_code: str,
) -> dict[str, Any]:
    normalized_code = train_code.strip().upper()

    exact = [
        row
        for row in rows
        if str(row.get("station_train_code") or "").upper() == normalized_code
        or str(row.get("train_no") or "").upper() == normalized_code
    ]
    if exact:
        return exact[0]

    prefix = [
        row
        for row in rows
        if str(row.get("station_train_code") or "").upper().startswith(normalized_code)
    ]
    if prefix:
        return prefix[0]

    raise TaskExecutionError(f"未找到车次 {train_code} 在 {run_date} 的基础信息")


def derive_train_rows_from_stops(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    counts: dict[str, int] = {}
    for row in rows:
        train_no = str(row.get("train_no") or "").strip()
        if not train_no:
            continue
        grouped.setdefault(
            train_no,
            {
                "train_no": train_no,
                "station_train_code": row.get("station_train_code"),
                "from_station": row.get("start_station_name"),
                "to_station": row.get("end_station_name"),
                "total_num": None,
            },
        )
        counts[train_no] = counts.get(train_no, 0) + 1

    for train_no, count in counts.items():
        grouped[train_no]["total_num"] = count

    return list(grouped.values())


def derive_train_rows_from_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dedup: dict[str, dict[str, Any]] = {}
    for row in rows:
        train_no = str(row.get("train_no") or "").strip()
        if not train_no:
            continue
        dedup[train_no] = {
            "train_no": train_no,
            "station_train_code": row.get("station_train_code"),
            "from_station": row.get("from_station"),
            "to_station": row.get("to_station"),
            "total_num": row.get("total_num"),
        }
    return list(dedup.values())


def build_train_run_rows(
    raw_rows: list[dict[str, Any]],
    *,
    run_date: str,
    train_code: str,
) -> list[dict[str, Any]]:
    normalized_code = train_code.strip().upper()
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        station_train_code = str(row.get("station_train_code") or "").upper()
        train_no = str(row.get("train_no") or "").upper()
        if station_train_code != normalized_code and train_no != normalized_code:
            continue
        rows.append(
            {
                "train_no": row.get("train_no"),
                "station_train_code": row.get("station_train_code"),
                "from_station": row.get("from_station"),
                "to_station": row.get("to_station"),
                "total_num": row.get("total_num"),
                "run_date": run_date,
                "status": run_status_from_flag(row.get("data_flag")),
            }
        )
    return rows


def run_status_from_flag(value: Any) -> str:
    text = str(value if value is not None else "").strip().lower()
    if text in {"", "none", "null", "1", "true", "t", "yes", "y", "on"}:
        return "running"
    if text in {"0", "false", "f", "no", "n", "off"}:
        return "suspended"
    if "suspend" in text or "cancel" in text:
        return "suspended"
    return "unknown"
