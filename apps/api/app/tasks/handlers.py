from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import asyncpg

from app.integrations.crawler.client import AbstractCrawlerClient, seed_keywords
from app.integrations.geo.client import AbstractGeoClient
from app.models import TaskDefinition
from app.railway.repository import (
    RailwayTaskRepository,
    StationRepository,
    dedupe_train_rows,
)
from app.system.log_repository import LogRepository
from app.tasks.exceptions import TaskExecutionError
from app.tasks.progress import build_progress_snapshot
from app.tasks.repository import TaskRunLogRepository, TaskRunRepository
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
    progress_snapshot: dict[str, Any] | None = None


@dataclass
class FetchTrainsProgressStats:
    total_seed_keywords: int = 0
    current_seed_keyword: str | None = None
    completed_seed_keywords: int = 0
    failed_seed_keywords: int = 0
    last_completed_seed_keyword: str | None = None
    last_failed_seed_keyword: str | None = None
    raw_rows_fetched: int = 0
    unique_train_nos_seen: int = 0
    trains_upsert_attempted: int = 0
    duplicate_rows_skipped: int = 0

    def to_snapshot(
        self,
        *,
        stage: str = "crawling",
        status: str = "running",
    ) -> dict[str, Any]:
        processed_units = self.completed_seed_keywords + self.failed_seed_keywords
        pending_units = max(0, self.total_seed_keywords - processed_units)
        return build_progress_snapshot(
            "fetch-trains",
            stage=stage,
            status=status,
            summary={
                "processedUnits": processed_units,
                "pendingUnits": pending_units,
                "successUnits": self.completed_seed_keywords,
                "failedUnits": self.failed_seed_keywords,
            },
            details={
                "currentSeedKeyword": self.current_seed_keyword,
                "pendingSeedKeywords": pending_units,
                "completedSeedKeywords": self.completed_seed_keywords,
                "failedSeedKeywords": self.failed_seed_keywords,
                "lastCompletedSeedKeyword": self.last_completed_seed_keyword,
                "lastFailedSeedKeyword": self.last_failed_seed_keyword,
                "rawRowsFetched": self.raw_rows_fetched,
                "uniqueTrainNosSeen": self.unique_train_nos_seen,
                "trainsUpsertAttempted": self.trains_upsert_attempted,
                "duplicateRowsSkipped": self.duplicate_rows_skipped,
            },
        )


@dataclass
class HandlerContext:
    task: TaskDefinition
    run_id: int
    pool: asyncpg.Pool
    run_repo: TaskRunRepository
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
    keyword_display = payload.keyword or "<roots>"
    seeds = [payload.keyword] if payload.keyword else seed_keywords()
    await ctx.log(
        "INFO",
        f"任务 {ctx.task.name} 开始抓取车次：date={payload.date}, keyword={keyword_display}",
    )

    repo = RailwayTaskRepository(ctx.pool)
    stats = FetchTrainsProgressStats(total_seed_keywords=len(seeds))
    seen_train_nos: set[str] = set()

    for seed in seeds:
        stats.current_seed_keyword = seed
        try:
            rows = await ctx.crawler_client.fetch_trains(payload.date, seed)
        except Exception as exc:
            stats.failed_seed_keywords += 1
            stats.last_failed_seed_keyword = seed
            snapshot = stats.to_snapshot()
            await ctx.run_repo.update_progress_snapshot(ctx.run_id, snapshot)
            await ctx.log(
                "WARN",
                (
                    "fetch-trains seed failed: "
                    f"keyword={seed} pending={snapshot['summary']['pendingUnits']} "
                    f"error={exc}"
                ),
            )
            continue

        stats.raw_rows_fetched += len(rows)
        deduped_rows = dedupe_train_rows(rows)
        duplicate_count = len(rows) - len(deduped_rows)
        new_rows: list[dict[str, Any]] = []
        for row in deduped_rows:
            train_no = str(row.get("train_no") or "").strip()
            if not train_no:
                continue
            if train_no in seen_train_nos:
                duplicate_count += 1
                continue
            seen_train_nos.add(train_no)
            new_rows.append(row)

        upserted = 0
        if new_rows:
            upserted = await repo.upsert_train_rows(new_rows)
            stats.trains_upsert_attempted += len(new_rows)
            stats.unique_train_nos_seen += len(new_rows)
        stats.duplicate_rows_skipped += duplicate_count
        stats.completed_seed_keywords += 1
        stats.last_completed_seed_keyword = seed

        snapshot = stats.to_snapshot()
        await ctx.run_repo.update_progress_snapshot(ctx.run_id, snapshot)
        await ctx.log(
            "INFO",
            (
                "fetch-trains seed processed: "
                f"keyword={seed} fetched={len(rows)} deduped={len(deduped_rows)} "
                f"upserted={upserted} pending={snapshot['summary']['pendingUnits']} "
                f"completed={stats.completed_seed_keywords}"
            ),
        )

    if stats.unique_train_nos_seen == 0 and stats.failed_seed_keywords == 0:
        await ctx.log(
            "INFO",
            f"fetch-trains 完成，但未找到匹配车次：keyword={keyword_display}",
        )
        return TaskExecutionResult(
            summary="车次同步完成，未找到匹配数据",
            metrics_value="0",
            progress_snapshot=stats.to_snapshot(),
        )

    if stats.failed_seed_keywords > 0:
        await ctx.log(
            "WARN",
            (
                "fetch-trains 完成，但存在失败种子关键词："
                f"failed={stats.failed_seed_keywords}, "
                f"last={stats.last_failed_seed_keyword or '-'}"
            ),
        )
        summary = "车次同步完成，部分种子关键词抓取失败"
    else:
        summary = "车次同步完成"

    await ctx.log("SUCCESS", f"fetch-trains 完成，写入 {stats.unique_train_nos_seen} 条车次记录")
    return TaskExecutionResult(
        summary=summary,
        metrics_value=str(stats.unique_train_nos_seen),
        progress_snapshot=stats.to_snapshot(),
    )


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
    normalized_run_date = run_date.strip()
    normalized_code = train_code.strip().upper()
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        station_train_code = str(row.get("station_train_code") or "").strip().upper()
        if not station_train_code or not station_train_code.startswith(normalized_code):
            continue

        row_run_date = str(row.get("run_date") or "").strip()
        row_compact_date = str(row.get("date") or "").strip()
        if row_run_date:
            normalized_row_run_date = row_run_date
        elif len(row_compact_date) == 8 and row_compact_date.isdigit():
            normalized_row_run_date = (
                f"{row_compact_date[:4]}-{row_compact_date[4:6]}-{row_compact_date[6:8]}"
            )
        else:
            normalized_row_run_date = ""

        if normalized_row_run_date != normalized_run_date:
            continue

        rows.append(
            {
                "train_no": row.get("train_no"),
                "station_train_code": row.get("station_train_code"),
                "from_station": row.get("from_station"),
                "to_station": row.get("to_station"),
                "total_num": row.get("total_num"),
                "run_date": normalized_run_date,
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
