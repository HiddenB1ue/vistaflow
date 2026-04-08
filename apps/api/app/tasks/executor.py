from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from app.tasks.execution import TaskExecutionContext, TaskExecutionResult

PayloadModelT = TypeVar("PayloadModelT", bound=BaseModel)


class TaskExecutorHelper:
    def __init__(self, ctx: TaskExecutionContext) -> None:
        self._ctx = ctx
        self._summary = {
            "totalUnits": 0,
            "processedUnits": 0,
            "successUnits": 0,
            "failedUnits": 0,
            "pendingUnits": 0,
            "warningUnits": 0,
        }
        self._current: dict[str, Any] = {}
        self._last_error: dict[str, Any] = {}
        self._details: dict[str, Any] = {}

    def parse_payload(self, payload_model: type[PayloadModelT]) -> PayloadModelT:
        return payload_model.model_validate(self._ctx.task.payload)

    async def begin(
        self,
        message: str,
        *,
        total_units: int = 0,
        current: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._summary["totalUnits"] = total_units
        self._summary["pendingUnits"] = total_units
        if current is not None:
            self._current = dict(current)
        if details is not None:
            self._details = dict(details)
        await self._ctx.log("INFO", message)
        snapshot = self.snapshot()
        await self._ctx.update_progress(snapshot)
        return snapshot

    async def checkpoint(self) -> None:
        await self._ctx.raise_if_cancel_requested()

    async def update(
        self,
        *,
        phase: str = "processing",
        status: str = "running",
        summary: dict[str, int] | None = None,
        current: dict[str, Any] | None = None,
        last_error: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if summary is not None:
            self._summary.update({key: int(value) for key, value in summary.items()})
        if current is not None:
            self._current = dict(current)
        if last_error is not None:
            self._last_error = dict(last_error)
        if details is not None:
            self._details.update(details)
        snapshot = self.snapshot(phase=phase, status=status)
        await self._ctx.update_progress(snapshot)
        return snapshot

    def snapshot(
        self,
        *,
        phase: str = "processing",
        status: str = "running",
    ) -> dict[str, Any]:
        return self._ctx.build_progress_snapshot(
            phase=phase,
            status=status,
            summary=self._summary,
            current=self._current,
            last_error=self._last_error,
            details=self._details,
        )

    def success(
        self,
        *,
        summary: str,
        metrics_value: str = "",
        timing_value: str = "",
    ) -> TaskExecutionResult:
        return TaskExecutionResult(
            summary=summary,
            result_level="success",
            metrics_value=metrics_value,
            timing_value=timing_value,
            progress_snapshot=self.snapshot(),
        )

    def warning(
        self,
        *,
        summary: str,
        metrics_value: str = "",
        timing_value: str = "",
    ) -> TaskExecutionResult:
        return TaskExecutionResult(
            summary=summary,
            result_level="warning",
            metrics_value=metrics_value,
            timing_value=timing_value,
            progress_snapshot=self.snapshot(),
        )
