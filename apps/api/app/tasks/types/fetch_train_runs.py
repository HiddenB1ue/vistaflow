from __future__ import annotations

from app.railway.repository import RailwayTaskRepository
from app.tasks.definition import TaskCapabilityContract, TaskTypeDefinition
from app.tasks.exceptions import TaskExecutionError
from app.tasks.execution import TaskExecutionContext
from app.tasks.executor import TaskExecutorHelper
from app.tasks.payloads import FetchTrainRunsPayload
from app.tasks.railway_support import build_train_run_rows, derive_train_rows_from_runs
from app.tasks.type_params import TRAIN_CODE_PARAM, TRAIN_DATE_PARAM


async def execute_fetch_train_runs(ctx: TaskExecutionContext):
    helper = TaskExecutorHelper(ctx)
    payload = helper.parse_payload(FetchTrainRunsPayload)
    await helper.begin(
        f"任务 {ctx.task.name} 开始抓取运行车次：date={payload.date}, train_code={payload.train_code}",
        total_units=1,
        current={"unitId": payload.train_code, "label": payload.train_code},
        details={"requestedDate": payload.date},
    )
    await helper.checkpoint()
    raw_rows = await ctx.crawler_client.fetch_train_runs(payload.date, payload.train_code)
    run_rows = build_train_run_rows(
        raw_rows,
        run_date=payload.date,
        train_code=payload.train_code,
    )
    if not run_rows:
        raise TaskExecutionError(f"未找到车次 {payload.train_code} 在 {payload.date} 的运行事实")

    train_rows = derive_train_rows_from_runs(run_rows)
    await helper.checkpoint()
    repo = RailwayTaskRepository(ctx.pool)
    train_count, run_count = await repo.upsert_train_and_run_rows(train_rows, run_rows)
    await helper.update(
        summary={
            "processedUnits": 1,
            "successUnits": 1,
            "pendingUnits": 0,
        },
        current={"unitId": payload.train_code, "label": payload.train_code},
        details={"upsertedTrainRows": train_count, "upsertedRunRows": run_count},
    )
    await ctx.log(
        "SUCCESS",
        f"fetch-train-runs 完成，写入 {train_count} 条车次记录和 {run_count} 条运行记录",
    )
    return helper.success(summary="运行车次同步完成", metrics_value=str(run_count))


TASK_TYPE_DEFINITION = TaskTypeDefinition(
    type="fetch-train-runs",
    label="获取某天运行的车次",
    description="抓取指定车次前缀在某天的运行事实，并写入 train_runs 表。",
    implemented=True,
    capability=TaskCapabilityContract(),
    param_schema=(TRAIN_DATE_PARAM, TRAIN_CODE_PARAM),
    payload_model=FetchTrainRunsPayload,
    executor=execute_fetch_train_runs,
)
