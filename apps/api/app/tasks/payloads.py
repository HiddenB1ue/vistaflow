from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from app.tasks.exceptions import TaskPayloadValidationError

TASK_DATE_TIMEZONE = ZoneInfo("Asia/Shanghai")
MAX_DATE_OFFSET_DAYS = 60
TaskDateMode = Literal["fixed", "relative"]


class TrainDatePayloadMixin(BaseModel):
    date_mode: TaskDateMode = Field(default="fixed", alias="dateMode")
    date: str | None = None
    date_offset_days: int | None = Field(default=None, alias="dateOffsetDays")

    @field_validator("date")
    @classmethod
    def normalize_date_field(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_payload_date(value)

    @field_validator("date_offset_days")
    @classmethod
    def normalize_date_offset_field(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 0 or value > MAX_DATE_OFFSET_DAYS:
            raise ValueError(f"dateOffsetDays 必须在 0-{MAX_DATE_OFFSET_DAYS} 之间")
        return value

    @model_validator(mode="after")
    def validate_date_strategy(self) -> TrainDatePayloadMixin:
        if self.date_mode == "fixed":
            if self.date is None:
                raise ValueError("固定日期模式必须填写 date")
            self.date_offset_days = None
            return self
        if self.date_offset_days is None:
            raise ValueError("相对日期模式必须填写 dateOffsetDays")
        self.date = None
        return self

    def resolved_date(self, *, now: datetime | None = None) -> str:
        return resolve_train_payload_date(self, now=now)


class FetchTrainsPayload(TrainDatePayloadMixin):
    keyword: str | None = None

    @field_validator("keyword")
    @classmethod
    def normalize_keyword_field(cls, value: str | None) -> str | None:
        return normalize_optional_text_field(value)


class FetchTrainStopsPayload(TrainDatePayloadMixin):
    keyword: str | None = None

    @field_validator("keyword")
    @classmethod
    def normalize_keyword_field(cls, value: str | None) -> str | None:
        return normalize_optional_text_field(value)


class FetchTrainRunsPayload(TrainDatePayloadMixin):
    keyword: str | None = None

    @field_validator("keyword")
    @classmethod
    def normalize_keyword_field(cls, value: str | None) -> str | None:
        return normalize_optional_text_field(value)


class FetchStationGeoPayload(BaseModel):
    address: str | None = None

    @field_validator("address")
    @classmethod
    def normalize_address_field(cls, value: str | None) -> str | None:
        return normalize_optional_text_field(value)


PayloadModel = type[BaseModel]


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


def resolve_train_payload_date(
    payload: TrainDatePayloadMixin,
    *,
    now: datetime | None = None,
) -> str:
    if payload.date_mode == "fixed":
        if payload.date is None:
            raise ValueError("固定日期模式必须填写 date")
        return payload.date
    base = now or datetime.now(TASK_DATE_TIMEZONE)
    if base.tzinfo is None:
        base = base.replace(tzinfo=TASK_DATE_TIMEZONE)
    local_base = base.astimezone(TASK_DATE_TIMEZONE)
    offset = payload.date_offset_days
    if offset is None:
        raise ValueError("相对日期模式必须填写 dateOffsetDays")
    return (local_base.date() + timedelta(days=offset)).isoformat()


def normalize_task_payload_with_model(
    task_type: str,
    payload: dict[str, Any],
    model: PayloadModel | None,
) -> dict[str, Any]:
    if model is None:
        return dict(payload)
    try:
        validated = model.model_validate(payload)
    except Exception as exc:
        raise TaskPayloadValidationError(task_type, str(exc)) from exc
    return dict(validated.model_dump(exclude_none=True, by_alias=True))
