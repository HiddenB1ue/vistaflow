from __future__ import annotations

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
