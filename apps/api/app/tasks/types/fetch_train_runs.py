from __future__ import annotations

from app.integrations.crawler.client import seed_keywords
from app.railway.repository import RailwayTaskRepository
from app.tasks.definition import TaskCapabilityContract, TaskTypeDefinition
from app.tasks.exceptions import TaskExecutionError
from app.tasks.execution import TaskExecutionContext
from app.tasks.executor import TaskExecutorHelper
from app.tasks.payloads import FetchTrainRunsPayload
from app.tasks.railway_support import build_train_run_rows, derive_train_rows_from_runs
from app.tasks.type_params import TRAIN_DATE_PARAM, TRAIN_KEYWORD_PARAM


async def execute_fetch_train_runs(ctx: TaskExecutionContext):
    helper = TaskExecutorHelper(ctx)
    payload = helper.parse_payload(FetchTrainRunsPayload)
    resolved_date = payload.resolved_date()
    keyword_display = payload.keyword or "<roots>"
    seeds = [payload.keyword] if payload.keyword else seed_keywords()
    repo = RailwayTaskRepository(ctx.pool)
    await helper.begin(
        f"任务 {ctx.task.name} 开始抓取运行车次：date={resolved_date}, keyword={keyword_display}",
        total_units=len(seeds),
        current={"unitId": keyword_display, "label": keyword_display},
        details={
            "requestedDate": payload.date,
            "dateMode": payload.date_mode,
            "dateOffsetDays": payload.date_offset_days,
            "resolvedDate": resolved_date,
        },
    )

    total_train_count = 0
    total_run_count = 0
    total_raw_rows = 0
    success_count = 0
    failed_count = 0
    last_failed_keyword: str | None = None

    for index, seed in enumerate(seeds, start=1):
        await helper.checkpoint()
        try:
            raw_rows = await ctx.crawler_client.fetch_train_runs(resolved_date, seed)
            total_raw_rows += len(raw_rows)
            run_rows = build_train_run_rows(
                raw_rows,
                run_date=resolved_date,
                keyword=seed,
            )
            train_rows = derive_train_rows_from_runs(run_rows)
            train_count = 0
            run_count = 0
            if run_rows:
                train_count, run_count = await repo.upsert_train_and_run_rows(train_rows, run_rows)
                total_train_count += train_count
                total_run_count += run_count
            success_count += 1
            await helper.update(
                summary={
                    "processedUnits": index,
                    "successUnits": success_count,
                    "failedUnits": failed_count,
                    "pendingUnits": len(seeds) - index,
                    "warningUnits": failed_count,
                },
                current={"unitId": seed, "label": seed},
                details={
                    "rawRowsFetched": total_raw_rows,
                    "upsertedTrainRows": total_train_count,
                    "upsertedRunRows": total_run_count,
                },
            )
            await ctx.log(
                "INFO",
                (
                    "fetch-train-runs seed processed: "
                    f"keyword={seed} fetched={len(raw_rows)} matched={len(run_rows)} "
                    f"upserted_train={train_count} upserted_run={run_count}"
                ),
            )
        except Exception as exc:
            failed_count += 1
            last_failed_keyword = seed
            await helper.update(
                summary={
                    "processedUnits": index,
                    "successUnits": success_count,
                    "failedUnits": failed_count,
                    "pendingUnits": len(seeds) - index,
                    "warningUnits": failed_count,
                },
                current={"unitId": seed, "label": seed},
                last_error={"unitId": seed, "label": seed, "message": str(exc)},
                details={
                    "rawRowsFetched": total_raw_rows,
                    "upsertedTrainRows": total_train_count,
                    "upsertedRunRows": total_run_count,
                },
            )
            await ctx.log(
                "WARN",
                f"fetch-train-runs seed failed: keyword={seed} error={exc}",
            )

    if total_run_count == 0:
        raise TaskExecutionError(f"未找到关键字 {keyword_display} 在 {resolved_date} 的运行事实")

    if failed_count > 0:
        await ctx.log(
            "WARN",
            (
                "fetch-train-runs 完成，但存在失败种子关键词："
                f"failed={failed_count}, last={last_failed_keyword or '-'}"
            ),
        )
        summary = "运行车次同步完成，部分种子关键词抓取失败"
        result_builder = helper.warning
    else:
        summary = "运行车次同步完成"
        result_builder = helper.success

    await ctx.log(
        "SUCCESS",
        f"fetch-train-runs 完成，写入 {total_train_count} 条车次记录和 {total_run_count} 条运行记录",
    )
    return result_builder(summary=summary, metrics_value=str(total_run_count))


TASK_TYPE_DEFINITION = TaskTypeDefinition(
    type="fetch-train-runs",
    label="获取某天运行的车次",
    description="按日期和关键字抓取运行车次事实，并写入 train_runs 表。",
    implemented=True,
    capability=TaskCapabilityContract(),
    param_schema=(TRAIN_DATE_PARAM, TRAIN_KEYWORD_PARAM),
    payload_model=FetchTrainRunsPayload,
    executor=execute_fetch_train_runs,
)
