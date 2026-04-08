from __future__ import annotations

from app.railway.repository import StationRepository
from app.tasks.definition import TaskCapabilityContract, TaskTypeDefinition
from app.tasks.execution import TaskExecutionContext
from app.tasks.executor import TaskExecutorHelper


async def execute_fetch_station(ctx: TaskExecutionContext):
    helper = TaskExecutorHelper(ctx)
    await helper.begin(
        f"任务 {ctx.task.name} 开始抓取全国车站基础数据",
        total_units=1,
        current={"unitId": "stations", "label": "全国车站"},
    )
    await helper.checkpoint()
    stations = await ctx.crawler_client.fetch_stations()
    await helper.checkpoint()
    station_repo = StationRepository(ctx.pool)
    count = await station_repo.upsert_stations(stations)
    await helper.update(
        summary={
            "processedUnits": 1,
            "successUnits": 1,
            "pendingUnits": 0,
        },
        current={"unitId": "stations", "label": "全国车站"},
        details={"upsertedStations": count},
    )
    await ctx.log("SUCCESS", f"fetch-station 完成，写入 {count} 条记录")
    return helper.success(summary="站点基础数据同步完成", metrics_value=str(count))


TASK_TYPE_DEFINITION = TaskTypeDefinition(
    type="fetch-station",
    label="站点主数据同步",
    description="从 12306 抓取全国车站基础数据并写入 stations 表。",
    implemented=True,
    capability=TaskCapabilityContract(),
    executor=execute_fetch_station,
)
