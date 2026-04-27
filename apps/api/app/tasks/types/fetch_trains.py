from __future__ import annotations

from typing import Any

from app.integrations.crawler.client import seed_keywords
from app.railway.repository import RailwayTaskRepository, dedupe_train_rows
from app.tasks.definition import TaskCapabilityContract, TaskTypeDefinition
from app.tasks.execution import TaskExecutionContext
from app.tasks.executor import TaskExecutorHelper
from app.tasks.payloads import FetchTrainsPayload
from app.tasks.railway_support import FetchTrainsProgressStats
from app.tasks.type_params import TRAIN_DATE_PARAM, TRAIN_KEYWORD_PARAM


async def execute_fetch_trains(ctx: TaskExecutionContext):
    helper = TaskExecutorHelper(ctx)
    payload = helper.parse_payload(FetchTrainsPayload)
    resolved_date = payload.resolved_date()
    keyword_display = payload.keyword or "<roots>"
    seeds = [payload.keyword] if payload.keyword else seed_keywords()
    await helper.begin(
        f"任务 {ctx.task.name} 开始抓取车次：date={resolved_date}, keyword={keyword_display}",
        total_units=len(seeds),
        current={"unitId": keyword_display, "label": keyword_display},
        details={
            "requestedDate": payload.date,
            "dateMode": payload.date_mode,
            "dateOffsetDays": payload.date_offset_days,
            "resolvedDate": resolved_date,
        },
    )

    repo = RailwayTaskRepository(ctx.pool)
    stats = FetchTrainsProgressStats(total_seed_keywords=len(seeds))
    seen_train_nos: set[str] = set()

    for seed in seeds:
        await helper.checkpoint()
        stats.current_seed_keyword = seed
        try:
            rows = await ctx.crawler_client.fetch_trains(resolved_date, seed)
        except Exception as exc:
            stats.failed_seed_keywords += 1
            stats.last_failed_seed_keyword = seed
            snapshot = stats.to_snapshot()
            await helper.update(
                summary=snapshot["summary"],
                current={"unitId": seed, "label": seed},
                last_error={"unitId": seed, "label": seed, "message": str(exc)},
                details=snapshot["details"],
            )
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
        await helper.update(
            summary=snapshot["summary"],
            current={"unitId": seed, "label": seed},
            details=snapshot["details"],
        )
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
        await ctx.log("INFO", f"fetch-trains 完成，但未找到匹配车次：keyword={keyword_display}")
        return helper.success(summary="车次同步完成，未找到匹配数据", metrics_value="0")

    if stats.failed_seed_keywords > 0:
        await ctx.log(
            "WARN",
            (
                "fetch-trains 完成，但存在失败种子关键词："
                f"failed={stats.failed_seed_keywords}, "
                f"last={stats.last_failed_seed_keyword or '-'}"
            ),
        )
        await helper.update(
            summary={"warningUnits": stats.failed_seed_keywords},
            details={"resultLevel": "warning"},
        )
        summary = "车次同步完成，部分种子关键词抓取失败"
        result_builder = helper.warning
    else:
        summary = "车次同步完成"
        result_builder = helper.success

    await ctx.log("SUCCESS", f"fetch-trains 完成，写入 {stats.unique_train_nos_seen} 条车次记录")
    return result_builder(summary=summary, metrics_value=str(stats.unique_train_nos_seen))


TASK_TYPE_DEFINITION = TaskTypeDefinition(
    type="fetch-trains",
    label="爬取车次",
    description="按日期和关键字抓取车次目录，并写入 trains 表。",
    implemented=True,
    capability=TaskCapabilityContract(),
    param_schema=(TRAIN_DATE_PARAM, TRAIN_KEYWORD_PARAM),
    payload_model=FetchTrainsPayload,
    executor=execute_fetch_trains,
)
