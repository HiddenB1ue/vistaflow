from __future__ import annotations

from typing import Final

from app.tasks.definition import TaskParamDefinition

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
    placeholder="例如 G、D3、K12",
    description="车次前缀关键字；留空时任务会按系统内置根关键字集合依次抓取。",
)

TRAIN_LOOKUP_KEYWORD_PARAM: Final[TaskParamDefinition] = TaskParamDefinition(
    key="keyword",
    label="关键字",
    value_type="text",
    required=False,
    placeholder="例如 G1 或 240000G1010A",
    description=(
        "用于数据库定位 train_no；可传 station_train_code 或 train_no，"
        "留空时处理库内全部车次。"
    ),
)

STATION_ADDRESS_PARAM: Final[TaskParamDefinition] = TaskParamDefinition(
    key="address",
    label="地址",
    value_type="text",
    required=False,
    placeholder="例如 上海虹桥站",
    description="手动输入地址时只查询该地址且不落库；留空时从 stations 表中批量补全缺失坐标。",
)
