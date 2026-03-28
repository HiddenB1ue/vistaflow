from __future__ import annotations

from pydantic import BaseModel


class APIResponse[T](BaseModel):
    success: bool
    data: T | None = None
    error: str | None = None

    @classmethod
    def ok(cls, data: T) -> APIResponse[T]:
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> APIResponse[None]:
        return APIResponse[None](success=False, error=error)
