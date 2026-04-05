from __future__ import annotations

from dataclasses import dataclass

import asyncpg

from app.integrations.crawler.client import AbstractCrawlerClient
from app.integrations.geo.client import AbstractGeoClient
from app.models import CrawlTask
from app.railway.repository import StationRepository
from app.system.log_repository import LogRepository
from app.tasks.repository import TaskRepository

GEO_SOURCE_AMAP = "amap_v3_geocode"


@dataclass
class HandlerContext:
    """所有 handler 共享的执行上下文，按需取用。"""
    task: CrawlTask
    pool: asyncpg.Pool
    task_repo: TaskRepository
    log_repo: LogRepository
    crawler_client: AbstractCrawlerClient
    geo_client: AbstractGeoClient


async def handle_fetch_station(ctx: HandlerContext) -> None:
    """抓取全国车站基础数据，通过 Repository 写入 stations 表。"""
    try:
        stations = await ctx.crawler_client.fetch_stations()
        station_repo = StationRepository(ctx.pool)
        count = await station_repo.upsert_stations(stations)
        await ctx.task_repo.update_status(
            ctx.task.id, "completed", metrics_value=str(count)
        )
        await ctx.log_repo.write_log(
            "SUCCESS",
            f"fetch-station 完成，写入 {count} 条记录",
            highlighted_terms=["fetch-station"],
        )
    except Exception as exc:
        await ctx.task_repo.update_status(
            ctx.task.id, "error", error_message=str(exc)
        )
        await ctx.log_repo.write_log(
            "ERROR",
            f"fetch-station 失败: {exc}",
            highlighted_terms=["fetch-station"],
        )


async def handle_geocode(ctx: HandlerContext) -> None:
    """查询坐标缺失站点，通过 Repository 解析并回写经纬度。"""
    try:
        station_repo = StationRepository(ctx.pool)
        rows = await station_repo.find_missing_geo()
        success_count = 0
        for row in rows:
            result = await ctx.geo_client.geocode_station(
                str(row["name"]), str(row.get("area_name") or "")
            )
            if result is not None:
                lng, lat = result
                await station_repo.update_geo(
                    int(row["id"]), lng, lat, GEO_SOURCE_AMAP
                )
                success_count += 1
        await ctx.task_repo.update_status(
            ctx.task.id, "completed", metrics_value=str(success_count)
        )
        await ctx.log_repo.write_log(
            "SUCCESS",
            f"geocode 完成，成功解析 {success_count} 个站点",
            highlighted_terms=["geocode"],
        )
    except Exception as exc:
        await ctx.task_repo.update_status(
            ctx.task.id, "error", error_message=str(exc)
        )
        await ctx.log_repo.write_log(
            "ERROR",
            f"geocode 失败: {exc}",
            highlighted_terms=["geocode"],
        )


async def handle_placeholder(ctx: HandlerContext) -> None:
    """占位 handler：fetch-status、price、cleanup。"""
    try:
        await ctx.task_repo.update_status(ctx.task.id, "completed")
        await ctx.log_repo.write_log(
            "INFO",
            f"{ctx.task.type} 任务完成（占位实现）",
            highlighted_terms=[ctx.task.type],
        )
    except Exception as exc:
        await ctx.task_repo.update_status(
            ctx.task.id, "error", error_message=str(exc)
        )
        await ctx.log_repo.write_log(
            "ERROR",
            f"{ctx.task.type} 失败: {exc}",
            highlighted_terms=[ctx.task.type],
        )
