from __future__ import annotations

from app.tasks.definition import TaskTypeDefinition
from app.tasks.types.fetch_station import TASK_TYPE_DEFINITION as FETCH_STATION_TASK
from app.tasks.types.fetch_train_runs import TASK_TYPE_DEFINITION as FETCH_TRAIN_RUNS_TASK
from app.tasks.types.fetch_train_stops import TASK_TYPE_DEFINITION as FETCH_TRAIN_STOPS_TASK
from app.tasks.types.fetch_trains import TASK_TYPE_DEFINITION as FETCH_TRAINS_TASK
from app.tasks.types.price import TASK_TYPE_DEFINITION as PRICE_TASK

BUILTIN_TASK_TYPES: tuple[TaskTypeDefinition, ...] = (
    FETCH_STATION_TASK,
    FETCH_TRAINS_TASK,
    FETCH_TRAIN_STOPS_TASK,
    FETCH_TRAIN_RUNS_TASK,
    PRICE_TASK,
)


def get_builtin_task_definitions() -> tuple[TaskTypeDefinition, ...]:
    return BUILTIN_TASK_TYPES
