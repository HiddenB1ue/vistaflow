from __future__ import annotations

from pydantic import BaseModel


class TaskMetrics(BaseModel):
    label: str
    value: str


class TaskTiming(BaseModel):
    label: str
    value: str


class TaskResponse(BaseModel):
    id: int
    name: str
    type: str
    typeLabel: str
    status: str
    description: str | None = None
    cron: str | None = None
    metrics: TaskMetrics
    timing: TaskTiming
    errorMessage: str | None = None
