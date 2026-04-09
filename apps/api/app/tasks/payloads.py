from __future__ import annotations

from datetime import date as date_type
from typing import Any

from pydantic import BaseModel, field_validator

from app.tasks.exceptions import TaskPayloadValidationError


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
    keyword: str | None = None

    @field_validator("date")
    @classmethod
    def normalize_date_field(cls, value: str) -> str:
        return normalize_payload_date(value)

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
    return dict(validated.model_dump(exclude_none=True))
