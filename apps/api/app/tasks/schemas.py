from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.tasks.constants import TaskParamDefinition
from app.tasks.exceptions import TaskPayloadValidationError


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
    startedAt: datetime | None = None
    finishedAt: datetime | None = None
    errorMessage: str | None = None


class TaskCreateRequest(BaseModel):
    name: str
    type: str
    description: str | None = None
    enabled: bool = True
    cron: str | None = None
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
    cron: str | None = None
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
    cron: str | None = None
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


class FetchTrainsPayload(BaseModel):
    date: str
    keyword: str | None = None

    @field_validator("date")
    @classmethod
    def normalize_date_field(cls, value: str) -> str:
        return normalize_payload_date(value)

    @field_validator("keyword")
    @classmethod
    def normalize_keyword_field(cls, value: str | None) -> str | None:
        return normalize_optional_text_field(value)


class FetchTrainStopsPayload(BaseModel):
    date: str
    keyword: str | None = None

    @field_validator("date")
    @classmethod
    def normalize_date_field(cls, value: str) -> str:
        return normalize_payload_date(value)

    @field_validator("keyword")
    @classmethod
    def normalize_keyword_field(cls, value: str | None) -> str | None:
        return normalize_optional_text_field(value)


class FetchTrainRunsPayload(BaseModel):
    date: str
    train_code: str

    @field_validator("date")
    @classmethod
    def normalize_date_field(cls, value: str) -> str:
        return normalize_payload_date(value)

    @field_validator("train_code")
    @classmethod
    def normalize_train_code_field(cls, value: str) -> str:
        return normalize_required_text_field(value, field_name="train_code")


TASK_PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    "fetch-trains": FetchTrainsPayload,
    "fetch-train-stops": FetchTrainStopsPayload,
    "fetch-train-runs": FetchTrainRunsPayload,
}


def normalize_required_text_field(value: str, *, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} 不能为空")
    return cleaned


def normalize_optional_text_field(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def normalize_payload_date(value: str) -> str:
    cleaned = value.strip()
    try:
        if len(cleaned) == 8 and cleaned.isdigit():
            parsed = date_type.fromisoformat(f"{cleaned[:4]}-{cleaned[4:6]}-{cleaned[6:]}")
        else:
            parsed = date_type.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError("日期必须是 YYYY-MM-DD 或 YYYYMMDD") from exc
    return parsed.isoformat()


def normalize_task_payload(task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    model = TASK_PAYLOAD_MODELS.get(task_type)
    if model is None:
        return dict(payload)
    try:
        validated = model.model_validate(payload)
    except Exception as exc:
        raise TaskPayloadValidationError(task_type, str(exc)) from exc
    return dict(validated.model_dump(exclude_none=True))


def get_task_payload_model(task_type: str) -> type[BaseModel] | None:
    return TASK_PAYLOAD_MODELS.get(task_type)


def build_task_param_response(definition: TaskParamDefinition) -> TaskParamResponse:
    return TaskParamResponse(
        key=definition.key,
        label=definition.label,
        valueType=definition.value_type,
        required=definition.required,
        placeholder=definition.placeholder,
        description=definition.description,
    )
