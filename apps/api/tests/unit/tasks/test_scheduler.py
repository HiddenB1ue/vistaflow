from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.tasks.exceptions import TaskCronValidationError
from app.tasks.scheduler import (
    TaskScheduler,
    next_scheduled_run_at,
    normalize_run_at,
    validate_cron_expression,
)


def test_validate_cron_expression_accepts_standard_five_field_cron() -> None:
    assert validate_cron_expression(" 0 3 * * * ") == "0 3 * * *"


def test_validate_cron_expression_rejects_invalid_cron() -> None:
    with pytest.raises(TaskCronValidationError):
        validate_cron_expression("not cron")


def test_next_scheduled_run_at_uses_asia_shanghai_timezone() -> None:
    base = datetime(2026, 4, 26, 18, 0, tzinfo=UTC)

    result = next_scheduled_run_at("0 3 * * *", after=base)

    assert result == datetime(2026, 4, 26, 19, 0, tzinfo=UTC)


def test_normalize_run_at_accepts_future_datetime() -> None:
    now = datetime(2026, 4, 27, 1, 0, tzinfo=UTC)
    run_at = datetime(2026, 4, 27, 2, 0, tzinfo=UTC)

    assert normalize_run_at(run_at, now=now) == run_at


def test_normalize_run_at_rejects_past_datetime() -> None:
    now = datetime(2026, 4, 27, 1, 0, tzinfo=UTC)

    with pytest.raises(TaskCronValidationError):
        normalize_run_at(datetime(2026, 4, 27, 0, 59, tzinfo=UTC), now=now)


@pytest.mark.asyncio
async def test_scheduler_enqueues_due_tasks() -> None:
    repo = AsyncMock()
    repo.enqueue_due_scheduled_runs.return_value = 1
    now = datetime(2026, 4, 27, 1, 0, tzinfo=UTC)
    scheduler = TaskScheduler(repo, now_factory=lambda: now)

    result = await scheduler.enqueue_due_tasks()

    assert result == 1
    repo.enqueue_due_scheduled_runs.assert_awaited_once()
    assert repo.enqueue_due_scheduled_runs.await_args.kwargs["now"] == now
    assert repo.enqueue_due_scheduled_runs.await_args.kwargs["requested_by"] == "scheduler"
