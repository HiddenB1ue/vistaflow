from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CredentialResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    health: str
    maskedKey: str
    quotaInfo: str | None = None
    expiryWarning: str | None = None


class LogResponse(BaseModel):
    id: int
    timestamp: str
    severity: str
    message: str
    highlightedTerms: list[str] | None = None


class SparklineResponse(BaseModel):
    values: list[int]
    labels: list[str]


class QuotaResponse(BaseModel):
    percentage: int
    used: int
    total: int


class ToggleResponse(BaseModel):
    id: str
    label: str
    description: str
    enabled: bool


class SystemSettingResponse(BaseModel):
    key: str
    value: Any
    valueType: str
    category: str
    label: str
    description: str | None = None
    enabled: bool
    updatedAt: datetime


class SystemSettingBatchUpdateItemRequest(BaseModel):
    key: str
    value: Any
    enabled: bool


class SystemSettingBatchUpdateRequest(BaseModel):
    items: list[SystemSettingBatchUpdateItemRequest]


class SystemSettingBatchUpdateResponse(BaseModel):
    updatedCount: int
    updatedKeys: list[str]
    updatedAt: datetime


class KpiStatsResponse(BaseModel):
    totalRecords: int
    stationCoverage: int
    coordCompletionRate: float
    pendingAlerts: int
    todayApiCalls: int
    remainingQuota: int


class ActiveTaskResponse(BaseModel):
    id: int
    name: str
    status: str
    elapsedTime: str | None = None
    startedAt: str | None = None


class SystemAlertResponse(BaseModel):
    id: int
    severity: str
    title: str
    message: str
    timestamp: str
