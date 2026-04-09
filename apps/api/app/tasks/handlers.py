from __future__ import annotations

from app.railway.repository import RailwayTaskRepository as _RailwayTaskRepository
from app.tasks.execution import TaskExecutionContext, TaskExecutionResult
from app.tasks.railway_support import (
    FetchTrainsProgressStats,
    build_train_run_rows,
    derive_train_rows_from_runs,
    resolve_stop_target_train_nos,
    run_status_from_flag,
)
from app.tasks.types import fetch_station as fetch_station_module
from app.tasks.types import fetch_station_geo as fetch_station_geo_module
from app.tasks.types import fetch_train_runs as fetch_train_runs_module
from app.tasks.types import fetch_train_stops as fetch_train_stops_module
from app.tasks.types import fetch_trains as fetch_trains_module

HandlerContext = TaskExecutionContext
RailwayTaskRepository = _RailwayTaskRepository
seed_keywords = fetch_trains_module.seed_keywords


async def handle_fetch_station(ctx: TaskExecutionContext) -> TaskExecutionResult:
    return await fetch_station_module.execute_fetch_station(ctx)


async def handle_fetch_station_geo(ctx: TaskExecutionContext) -> TaskExecutionResult:
    return await fetch_station_geo_module.execute_fetch_station_geo(ctx)


async def handle_fetch_trains(ctx: TaskExecutionContext) -> TaskExecutionResult:
    fetch_trains_module.RailwayTaskRepository = RailwayTaskRepository
    fetch_trains_module.seed_keywords = seed_keywords
    return await fetch_trains_module.execute_fetch_trains(ctx)


async def handle_fetch_train_stops(ctx: TaskExecutionContext) -> TaskExecutionResult:
    fetch_train_stops_module.RailwayTaskRepository = RailwayTaskRepository
    return await fetch_train_stops_module.execute_fetch_train_stops(ctx)


async def handle_fetch_train_runs(ctx: TaskExecutionContext) -> TaskExecutionResult:
    fetch_train_runs_module.RailwayTaskRepository = RailwayTaskRepository
    return await fetch_train_runs_module.execute_fetch_train_runs(ctx)


__all__ = [
    "FetchTrainsProgressStats",
    "HandlerContext",
    "RailwayTaskRepository",
    "TaskExecutionResult",
    "build_train_run_rows",
    "derive_train_rows_from_runs",
    "handle_fetch_station",
    "handle_fetch_station_geo",
    "handle_fetch_train_runs",
    "handle_fetch_train_stops",
    "handle_fetch_trains",
    "resolve_stop_target_train_nos",
    "run_status_from_flag",
    "seed_keywords",
]
