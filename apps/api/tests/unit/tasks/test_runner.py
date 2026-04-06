from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.models import TaskDefinition, TaskRun
from app.tasks.runner import TASK_HANDLERS, TaskRunner
from app.tasks.runtime import TaskRuntimeRegistry

NOW = datetime(2026, 4, 6, tzinfo=UTC)


def make_task(
    *,
    task_type: str = "fetch-station",
    payload: dict[str, object] | None = None,
) -> TaskDefinition:
    return TaskDefinition(
        id=1,
        name="任务",
        type=task_type,
        type_label=task_type,
        description="test",
        enabled=True,
        cron=None,
        payload=payload or {},
        status="idle",
        latest_run_id=None,
        latest_run_status=None,
        latest_run_started_at=None,
        latest_run_finished_at=None,
        latest_error_message=None,
        metrics_label="最近结果",
        metrics_value="",
        timing_label="最近耗时",
        timing_value="",
        error_message=None,
        created_at=NOW,
        updated_at=NOW,
    )


def make_run(*, status: str = "pending", task_type: str = "fetch-station") -> TaskRun:
    return TaskRun(
        id=11,
        task_id=1,
        task_name="任务",
        task_type=task_type,
        trigger_mode="manual",
        status=status,
        requested_by="admin",
        summary=None,
        metrics_value="",
        error_message=None,
        termination_reason=None,
        started_at=None,
        finished_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def runner_deps() -> tuple[
    TaskRunner,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    TaskRuntimeRegistry,
]:
    task_repo = AsyncMock()
    run_repo = AsyncMock()
    run_log_repo = AsyncMock()
    log_repo = AsyncMock()
    runtime = TaskRuntimeRegistry()
    runner = TaskRunner(
        pool=AsyncMock(),
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        log_repo=log_repo,
        runtime_registry=runtime,
        crawler_client=AsyncMock(),
        geo_client=AsyncMock(),
    )
    return runner, task_repo, run_repo, run_log_repo, log_repo, runtime


@pytest.mark.asyncio
async def test_execute_marks_completed(
    runner_deps: tuple[TaskRunner, AsyncMock, AsyncMock, AsyncMock, AsyncMock, TaskRuntimeRegistry],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, task_repo, run_repo, run_log_repo, _, _ = runner_deps

    async def fake_handler(ctx: object) -> object:
        return type(
            "Result",
            (),
            {"summary": "done", "metrics_value": "12", "timing_value": "1s"},
        )()

    monkeypatch.setitem(TASK_HANDLERS, "fetch-station", fake_handler)
    run_repo.find_by_id.return_value = make_run(status="completed")

    await runner.execute(make_task(), 11)

    task_repo.mark_task_running.assert_awaited_once_with(1, 11)
    task_repo.apply_run_result.assert_any_await(
        1,
        11,
        "completed",
        metrics_value="12",
        timing_value="1s",
    )
    run_log_repo.create_log.assert_awaited()


@pytest.mark.asyncio
async def test_execute_marks_error_when_handler_raises(
    runner_deps: tuple[TaskRunner, AsyncMock, AsyncMock, AsyncMock, AsyncMock, TaskRuntimeRegistry],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, task_repo, run_repo, _, log_repo, _ = runner_deps

    async def fake_handler(ctx: object) -> object:
        raise RuntimeError("boom")

    monkeypatch.setitem(TASK_HANDLERS, "fetch-trains", fake_handler)
    run_repo.find_by_id.return_value = make_run(status="error", task_type="fetch-trains")

    await runner.execute(make_task(task_type="fetch-trains"), 11)

    task_repo.apply_run_result.assert_any_await(
        1,
        11,
        "error",
        error_message="boom",
        timing_value=pytest.approx(
            task_repo.apply_run_result.await_args.kwargs["timing_value"], rel=0.0
        ),
    )
    log_repo.write_log.assert_awaited()


def test_runner_registers_railway_handlers() -> None:
    assert {"fetch-trains", "fetch-train-stops", "fetch-train-runs"}.issubset(TASK_HANDLERS)


@pytest.mark.asyncio
async def test_terminate_cancels_active_task(
    runner_deps: tuple[TaskRunner, AsyncMock, AsyncMock, AsyncMock, AsyncMock, TaskRuntimeRegistry],
) -> None:
    runner, _, run_repo, _, _, runtime = runner_deps
    gate = asyncio.Event()

    async def long_running() -> None:
        try:
            await gate.wait()
        except asyncio.CancelledError:
            return

    active_task = asyncio.create_task(long_running())
    runtime.register(11, 1, active_task)
    run_repo.find_by_id.return_value = make_run(status="terminated")

    result = await runner.terminate(make_run(status="running"))

    assert result.status == "terminated"
    assert active_task.cancelled() or active_task.done()
