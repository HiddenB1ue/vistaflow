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
    placeholder="例如 G、D、K、北京",
    description="递归抓取的起始关键字；留空时任务会按系统内置根关键字集合依次抓取。",
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

TRAIN_CODE_PARAM: Final[TaskParamDefinition] = TaskParamDefinition(
    key="train_code",
    label="车次",
    value_type="text",
    required=True,
    placeholder="例如 G1、D301",
    description="用于指定车次前缀或起始车次号，例如 G1 表示匹配 G1* 分支。",
)
