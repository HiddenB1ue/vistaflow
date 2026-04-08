from __future__ import annotations

from app.railway.repository import RailwayTaskRepository
from app.tasks.definition import TaskCapabilityContract, TaskTypeDefinition
from app.tasks.exceptions import TaskExecutionError
from app.tasks.execution import TaskExecutionContext
from app.tasks.executor import TaskExecutorHelper
from app.tasks.payloads import FetchTrainStopsPayload
from app.tasks.railway_support import resolve_stop_target_train_nos
from app.tasks.type_params import TRAIN_DATE_PARAM, TRAIN_LOOKUP_KEYWORD_PARAM


async def execute_fetch_train_stops(ctx: TaskExecutionContext):
    helper = TaskExecutorHelper(ctx)
    payload = helper.parse_payload(FetchTrainStopsPayload)
    keyword_display = payload.keyword or "<all>"
    repo = RailwayTaskRepository(ctx.pool)
    target_train_nos = await resolve_stop_target_train_nos(repo, payload.keyword)
    if not target_train_nos:
        if payload.keyword:
            raise TaskExecutionError(
                f"数据库中未找到关键字 {payload.keyword} 对应的车次，请先同步车次目录"
            )
        raise TaskExecutionError("数据库中没有可抓取经停的车次，请先执行 fetch-trains")

    await helper.begin(
        f"任务 {ctx.task.name} 开始抓取经停：date={payload.date}, keyword={keyword_display}",
        total_units=len(target_train_nos),
        current={"unitId": keyword_display, "label": keyword_display},
        details={"requestedDate": payload.date},
    )

    total_stop_count = 0
    success_count = 0
    failed_count = 0
    last_failed_train_no: str | None = None

    for index, train_no in enumerate(target_train_nos, start=1):
        await helper.checkpoint()
        try:
            stop_rows = await ctx.crawler_client.fetch_train_stops(train_no, payload.date)
            if not stop_rows:
                raise TaskExecutionError(f"未找到车次 {train_no} 在 {payload.date} 的经停数据")
            inserted = await repo.upsert_stop_rows(stop_rows)
            total_stop_count += inserted
            success_count += 1
            await helper.update(
                summary={
                    "processedUnits": index,
                    "successUnits": success_count,
                    "failedUnits": failed_count,
                    "pendingUnits": len(target_train_nos) - index,
                    "warningUnits": failed_count,
                },
                current={"unitId": train_no, "label": train_no},
                details={"upsertedStopRows": total_stop_count},
            )
            await ctx.log(
                "INFO",
                (
                    "fetch-train-stops target processed: "
                    f"train_no={train_no} fetched={len(stop_rows)} upserted={inserted}"
                ),
            )
        except Exception as exc:
            failed_count += 1
            last_failed_train_no = train_no
            await helper.update(
                summary={
                    "processedUnits": index,
                    "successUnits": success_count,
                    "failedUnits": failed_count,
                    "pendingUnits": len(target_train_nos) - index,
                    "warningUnits": failed_count,
                },
                current={"unitId": train_no, "label": train_no},
                last_error={"unitId": train_no, "label": train_no, "message": str(exc)},
                details={"upsertedStopRows": total_stop_count},
            )
            await ctx.log(
                "WARN",
                f"fetch-train-stops target failed: train_no={train_no} error={exc}",
            )

    if success_count == 0:
        suffix = f"，last={last_failed_train_no}" if last_failed_train_no else ""
        raise TaskExecutionError(f"车次经停抓取失败：success=0, failed={failed_count}{suffix}")

    if failed_count > 0:
        await ctx.log(
            "WARN",
            (
                "fetch-train-stops 完成，但存在失败车次："
                f"success={success_count}, failed={failed_count}, "
                f"last={last_failed_train_no or '-'}"
            ),
        )
        summary = "车次经停同步完成，部分车次抓取失败"
        result_builder = helper.warning
    else:
        summary = "车次经停同步完成"
        result_builder = helper.success

    await ctx.log(
        "SUCCESS",
        f"fetch-train-stops 完成，处理 {success_count} 个车次，写入 {total_stop_count} 条经停记录",
    )
    return result_builder(summary=summary, metrics_value=str(total_stop_count))


TASK_TYPE_DEFINITION = TaskTypeDefinition(
    type="fetch-train-stops",
    label="爬取车次经停",
    description="抓取指定车次或库内全部车次在某天的经停详情，并写入 train_stops 表。",
    implemented=True,
    capability=TaskCapabilityContract(),
    param_schema=(TRAIN_DATE_PARAM, TRAIN_LOOKUP_KEYWORD_PARAM),
    payload_model=FetchTrainStopsPayload,
    executor=execute_fetch_train_stops,
)
