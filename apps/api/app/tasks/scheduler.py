from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast
from zoneinfo import ZoneInfo

from croniter import CroniterBadCronError, croniter

from app.tasks.exceptions import TaskCronValidationError
from app.tasks.repository import TaskRepository

SCHEDULER_TIMEZONE = ZoneInfo("Asia/Shanghai")
SCHEDULER_REQUESTED_BY = "scheduler"


def validate_cron_expression(cron: str) -> str:
    cleaned = cron.strip()
    if not cleaned:
        raise TaskCronValidationError("表达式不能为空")
    try:
        if not croniter.is_valid(cleaned):
            raise TaskCronValidationError("请使用标准 5 段 Cron 表达式")
    except CroniterBadCronError as exc:
        raise TaskCronValidationError(str(exc)) from exc
    return cleaned


def next_scheduled_run_at(cron: str, *, after: datetime | None = None) -> datetime:
    base = after or datetime.now(UTC)
    if base.tzinfo is None:
        base = base.replace(tzinfo=UTC)
    local_base = base.astimezone(SCHEDULER_TIMEZONE)
    try:
        next_local = cast(datetime, croniter(cron, local_base).get_next(datetime))
    except CroniterBadCronError as exc:
        raise TaskCronValidationError(str(exc)) from exc
    if next_local.tzinfo is None:
        next_local = next_local.replace(tzinfo=SCHEDULER_TIMEZONE)
    return next_local.astimezone(UTC)


def normalize_run_at(run_at: datetime | None, *, now: datetime | None = None) -> datetime:
    if run_at is None:
        raise TaskCronValidationError("一次性执行时间不能为空")
    normalized = run_at
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=SCHEDULER_TIMEZONE)
    normalized = normalized.astimezone(UTC)
    base = now or datetime.now(UTC)
    if base.tzinfo is None:
        base = base.replace(tzinfo=UTC)
    if normalized <= base.astimezone(UTC):
        raise TaskCronValidationError("一次性执行时间必须晚于当前时间")
    return normalized


class TaskScheduler:
    def __init__(
        self,
        task_repo: TaskRepository,
        *,
        batch_size: int = 10,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._batch_size = batch_size
        self._now_factory = now_factory or (lambda: datetime.now(UTC))

    async def enqueue_due_tasks(self) -> int:
        now = self._now_factory()
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        return await self._task_repo.enqueue_due_scheduled_runs(
            now=now,
            limit=self._batch_size,
            requested_by=SCHEDULER_REQUESTED_BY,
            compute_next_run_at=lambda cron: next_scheduled_run_at(cron, after=now),
        )
