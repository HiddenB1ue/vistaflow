from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.tasks.definition import TaskParamDefinition
from app.tasks.registry import get_builtin_task_registry

TaskScheduleMode = Literal["manual", "once", "cron"]


class TaskMetrics(BaseModel):
    label: str
    value: str


class TaskTiming(BaseModel):
    label: str
    value: str


class TaskParamResponse(BaseModel):
    key: str
    label: str
    valueType: str
    required: bool
    placeholder: str
    description: str


class TaskTypeResponse(BaseModel):
    type: str
    label: str
    description: str
    implemented: bool
    supportsCron: bool
    paramSchema: list[TaskParamResponse] = Field(default_factory=list)


class TaskLatestRunResponse(BaseModel):
    id: int
    status: str
    resultLevel: str | None = None
    startedAt: datetime | None = None
    finishedAt: datetime | None = None
    errorMessage: str | None = None


class TaskCreateRequest(BaseModel):
    name: str
    type: str
    description: str | None = None
    enabled: bool = True
    scheduleMode: TaskScheduleMode | None = None
    cron: str | None = None
    runAt: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", "type")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("字段不能为空")
        return cleaned

    @field_validator("cron")
    @classmethod
    def normalize_cron(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class TaskUpdateRequest(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    enabled: bool | None = None
    scheduleMode: TaskScheduleMode | None = None
    cron: str | None = None
    runAt: datetime | None = None
    payload: dict[str, Any] | None = None

    @field_validator("name", "type")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("字段不能为空")
        return cleaned

    @field_validator("cron")
    @classmethod
    def normalize_optional_cron(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class TaskResponse(BaseModel):
    id: int
    name: str
    type: str
    typeLabel: str
    status: str
    description: str | None = None
    enabled: bool
    scheduleMode: TaskScheduleMode
    cron: str | None = None
    runAt: datetime | None = None
    nextRunAt: datetime | None = None
    payload: dict[str, Any]
    metrics: TaskMetrics
    timing: TaskTiming
    errorMessage: str | None = None
    latestRun: TaskLatestRunResponse | None = None


class TaskRunResponse(BaseModel):
    id: int
    taskId: int
    taskName: str
    taskType: str
    triggerMode: str
    status: str
    requestedBy: str
    summary: str | None = None
    resultLevel: str | None = None
    metricsValue: str = ""
    progressSnapshot: dict[str, Any] | None = None
    errorMessage: str | None = None
    terminationReason: str | None = None
    startedAt: datetime | None = None
    finishedAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime


class TaskRunLogResponse(BaseModel):
    id: int
    runId: int
    severity: str
    message: str
    createdAt: datetime


def normalize_task_payload(task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return get_builtin_task_registry().normalize_payload(task_type, payload)


def get_task_payload_model(task_type: str) -> type[BaseModel] | None:
    definition = get_builtin_task_registry().get_optional(task_type)
    return definition.payload_model if definition is not None else None


def build_task_param_response(definition: TaskParamDefinition) -> TaskParamResponse:
    return TaskParamResponse(
        key=definition.key,
        label=definition.label,
        valueType=definition.value_type,
        required=definition.required,
        placeholder=definition.placeholder,
        description=definition.description,
    )
