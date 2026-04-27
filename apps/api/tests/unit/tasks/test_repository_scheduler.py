from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.tasks.repository import TaskRepository


class FakeSchedulerConnection:
    def __init__(self, *, active: bool, schedule_mode: str = "cron") -> None:
        self.active = active
        self.schedule_mode = schedule_mode
        self.created_runs = 0
        self.marked_pending = 0
        self.skipped = 0
        self.cleared_once = 0

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()

    async def fetch(self, sql: str, *args: object) -> list[dict[str, object]]:
        return [
            {
                "id": 1,
                "type": "fetch-station",
                "schedule_mode": self.schedule_mode,
                "cron": "*/15 * * * *" if self.schedule_mode == "cron" else None,
            }
        ]

    async def fetchval(self, sql: str, *args: object) -> int | None:
        if "FROM task_run" in sql:
            return 1 if self.active else None
        if "INSERT INTO task_run" in sql:
            self.created_runs += 1
            assert "'scheduled'" in sql
            return 11
        return None

    async def execute(self, sql: str, *args: object) -> None:
        if "next_run_at = NULL" in sql:
            self.cleared_once += 1
            assert args[1] == 11
        elif "last_scheduled_at = $3" in sql:
            self.marked_pending += 1
            assert args[1] == 11
        elif "next_run_at = $2" in sql:
            self.skipped += 1


class FakeTransaction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class FakeAcquire:
    def __init__(self, conn: FakeSchedulerConnection) -> None:
        self._conn = conn

    async def __aenter__(self) -> FakeSchedulerConnection:
        return self._conn

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class FakePool:
    def __init__(self, conn: FakeSchedulerConnection) -> None:
        self._conn = conn

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self._conn)


@pytest.mark.asyncio
async def test_enqueue_due_scheduled_runs_creates_scheduled_run() -> None:
    conn = FakeSchedulerConnection(active=False)
    repo = TaskRepository(FakePool(conn))
    now = datetime(2026, 4, 27, 1, 0, tzinfo=UTC)

    queued = await repo.enqueue_due_scheduled_runs(
        now=now,
        limit=10,
        requested_by="scheduler",
        compute_next_run_at=lambda cron: now + timedelta(minutes=15),
    )

    assert queued == 1
    assert conn.created_runs == 1
    assert conn.marked_pending == 1
    assert conn.skipped == 0


@pytest.mark.asyncio
async def test_enqueue_due_scheduled_runs_skips_active_task_and_advances_schedule() -> None:
    conn = FakeSchedulerConnection(active=True)
    repo = TaskRepository(FakePool(conn))
    now = datetime(2026, 4, 27, 1, 0, tzinfo=UTC)

    queued = await repo.enqueue_due_scheduled_runs(
        now=now,
        limit=10,
        requested_by="scheduler",
        compute_next_run_at=lambda cron: now + timedelta(minutes=15),
    )

    assert queued == 0
    assert conn.created_runs == 0
    assert conn.marked_pending == 0
    assert conn.skipped == 1


@pytest.mark.asyncio
async def test_enqueue_due_once_run_clears_next_run_after_enqueue() -> None:
    conn = FakeSchedulerConnection(active=False, schedule_mode="once")
    repo = TaskRepository(FakePool(conn))
    now = datetime(2026, 4, 27, 1, 0, tzinfo=UTC)

    queued = await repo.enqueue_due_scheduled_runs(
        now=now,
        limit=10,
        requested_by="scheduler",
        compute_next_run_at=lambda cron: now + timedelta(minutes=15),
    )

    assert queued == 1
    assert conn.created_runs == 1
    assert conn.marked_pending == 0
    assert conn.cleared_once == 1
    assert conn.skipped == 0


@pytest.mark.asyncio
async def test_enqueue_due_once_run_keeps_next_run_when_active() -> None:
    conn = FakeSchedulerConnection(active=True, schedule_mode="once")
    repo = TaskRepository(FakePool(conn))
    now = datetime(2026, 4, 27, 1, 0, tzinfo=UTC)

    queued = await repo.enqueue_due_scheduled_runs(
        now=now,
        limit=10,
        requested_by="scheduler",
        compute_next_run_at=lambda cron: now + timedelta(minutes=15),
    )

    assert queued == 0
    assert conn.created_runs == 0
    assert conn.marked_pending == 0
    assert conn.cleared_once == 0
    assert conn.skipped == 0
