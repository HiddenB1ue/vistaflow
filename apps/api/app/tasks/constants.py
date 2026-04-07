from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Literal

TaskType = Literal[
    "fetch-station",
    "fetch-trains",
    "fetch-train-stops",
    "fetch-train-runs",
    "price",
]
TaskStatus = Literal["idle", "running", "completed", "error", "terminated"]
TaskRunStatus = Literal["pending", "running", "completed", "error", "terminated"]
TaskTriggerMode = Literal["manual"]
TaskValueType = Literal["date", "text"]


@dataclass(frozen=True)
class TaskParamDefinition:
    key: str
    label: str
    value_type: TaskValueType
    required: bool
    placeholder: str
    description: str


@dataclass(frozen=True)
class TaskTypeDefinition:
    type: str
    label: str
    description: str
    implemented: bool
    supports_cron: bool = True
    param_schema: tuple[TaskParamDefinition, ...] = field(default_factory=tuple)


TRAIN_DATE_PARAM: Final[TaskParamDefinition] = TaskParamDefinition(
    key="date",
    label="日期",
    value_type="date",
    required=True,
    placeholder="2026-04-05",
    description="支持 YYYY-MM-DD 或 YYYYMMDD，保存时统一为 YYYY-MM-DD。",
)

TRAIN_KEYWORD_PARAM: Final[TaskParamDefinition] = TaskParamDefinition(
    key="keyword",
    label="关键字",
    value_type="text",
    required=False,
    placeholder="例如 G、D、K、北京",
    description="递归抓取的起始关键字；留空时任务会按系统内置根关键字集合依次抓取。",
)

TRAIN_LOOKUP_KEYWORD_PARAM: Final[TaskParamDefinition] = TaskParamDefinition(
    key="keyword",
    label="关键字",
    value_type="text",
    required=False,
    placeholder="例如 G1 或 240000G1010A",
    description="用于数据库定位 train_no；可传 station_train_code 或 train_no，留空时处理库内全部车次。",
)

TRAIN_CODE_PARAM: Final[TaskParamDefinition] = TaskParamDefinition(
    key="train_code",
    label="车次",
    value_type="text",
    required=True,
    placeholder="例如 G1、D301",
    description="用于指定车次前缀或起始车次号，例如 G1 表示匹配 G1* 分支。",
)


TASK_TYPES: Final[dict[str, TaskTypeDefinition]] = {
    "fetch-station": TaskTypeDefinition(
        type="fetch-station",
        label="站点主数据同步",
        description="从 12306 抓取全国车站基础数据并写入 stations 表。",
        implemented=True,
    ),
    "fetch-trains": TaskTypeDefinition(
        type="fetch-trains",
        label="爬取车次",
        description="按日期和关键字抓取车次目录，并写入 trains 表。",
        implemented=True,
        param_schema=(TRAIN_DATE_PARAM, TRAIN_KEYWORD_PARAM),
    ),
    "fetch-train-stops": TaskTypeDefinition(
        type="fetch-train-stops",
        label="爬取车次经停",
        description="抓取指定车次或库内全部车次在某天的经停详情，并写入 train_stops 表。",
        implemented=True,
        param_schema=(TRAIN_DATE_PARAM, TRAIN_LOOKUP_KEYWORD_PARAM),
    ),
    "fetch-train-runs": TaskTypeDefinition(
        type="fetch-train-runs",
        label="获取某天运行的车次",
        description="抓取指定车次前缀在某天的运行事实，并写入 train_runs 表。",
        implemented=True,
        param_schema=(TRAIN_DATE_PARAM, TRAIN_CODE_PARAM),
    ),
    "price": TaskTypeDefinition(
        type="price",
        label="获取某个车次行程的余票信息",
        description="预留的余票查询任务类型，后续将接入 Redis 做实时缓存，当前暂未实现。",
        implemented=False,
    ),
}


RUNNABLE_TASK_TYPES: Final[frozenset[str]] = frozenset(
    task_type
    for task_type, definition in TASK_TYPES.items()
    if definition.implemented
)


def get_task_type_definition(task_type: str) -> TaskTypeDefinition | None:
    return TASK_TYPES.get(task_type)


def get_task_type_label(task_type: str) -> str:
    definition = get_task_type_definition(task_type)
    return definition.label if definition is not None else task_type


def get_task_type_param_schema(task_type: str) -> tuple[TaskParamDefinition, ...]:
    definition = get_task_type_definition(task_type)
    return definition.param_schema if definition is not None else ()


def is_supported_task_type(task_type: str) -> bool:
    return task_type in TASK_TYPES


def is_implemented_task_type(task_type: str) -> bool:
    definition = get_task_type_definition(task_type)
    return definition.implemented if definition is not None else False
