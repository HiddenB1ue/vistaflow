from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.models import TaskDefinition, TaskRun
from app.tasks.definition import TaskCapabilityContract, TaskTypeDefinition
from app.tasks.execution import TaskExecutionResult
from app.tasks.registry import TaskDefinitionRegistry
from app.tasks.runner import TaskRunner

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
        schedule_mode="manual",
        cron=None,
        payload=payload or {},
        status="pending",
        latest_run_id=11,
        latest_run_status="pending",
        latest_run_started_at=None,
        latest_run_finished_at=None,
        latest_error_message=None,
        latest_result_level=None,
        metrics_label="最近结果",
        metrics_value="",
        timing_label="最近耗时",
        timing_value="",
        error_message=None,
        created_at=NOW,
        updated_at=NOW,
    )


def make_run(
    *,
    status: str = "pending",
    task_type: str = "fetch-station",
    result_level: str | None = None,
    cancel_requested: bool = False,
) -> TaskRun:
    return TaskRun(
        id=11,
        task_id=1,
        task_name="任务",
        task_type=task_type,
        trigger_mode="manual",
        status=status,
        requested_by="admin",
        summary=None,
        result_level=result_level,
        metrics_value="",
        progress_snapshot=None,
        error_message=None,
        termination_reason=None,
        worker_id="worker-1",
        heartbeat_at=None,
        cancel_requested=cancel_requested,
        cancel_requested_at=None,
        started_at=None,
        finished_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


def make_registry(**handlers: object) -> TaskDefinitionRegistry:
    definitions = tuple(
        TaskTypeDefinition(
            type=task_type,
            label=task_type,
            description=task_type,
            implemented=True,
            capability=TaskCapabilityContract(),
            executor=handler,
        )
        for task_type, handler in handlers.items()
    )
    return TaskDefinitionRegistry(definitions)


@pytest.fixture
def runner_deps() -> tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
    task_repo = AsyncMock()
    run_repo = AsyncMock()
    run_log_repo = AsyncMock()
    log_repo = AsyncMock()
    return task_repo, run_repo, run_log_repo, log_repo


def build_runner(
    *,
    task_registry: TaskDefinitionRegistry,
    task_repo: AsyncMock,
    run_repo: AsyncMock,
    run_log_repo: AsyncMock,
    log_repo: AsyncMock,
) -> TaskRunner:
    return TaskRunner(
        pool=AsyncMock(),
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        log_repo=log_repo,
        task_registry=task_registry,
        crawler_client=AsyncMock(),
        geo_client=AsyncMock(),
        worker_id="worker-1",
        heartbeat_interval_seconds=60.0,
    )


@pytest.mark.asyncio
async def test_execute_marks_completed(
    runner_deps: tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_repo, run_repo, run_log_repo, log_repo = runner_deps

    async def fake_handler(ctx: object) -> TaskExecutionResult:
        return TaskExecutionResult(summary="done", metrics_value="12", timing_value="1s")

    runner = build_runner(
        task_registry=make_registry(**{"fetch-station": fake_handler}),
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        log_repo=log_repo,
    )
    task_repo.find_by_id.return_value = make_task()
    run_repo.update_run_status.return_value = make_run(status="completed", result_level="success")

    await runner.execute(make_run())

    task_repo.mark_task_running.assert_awaited_once_with(1, 11)
    task_repo.apply_run_result.assert_any_await(
        1,
        11,
        "completed",
        result_level="success",
        metrics_value="12",
        timing_value="1s",
    )
    run_log_repo.create_log.assert_awaited()
    log_repo.write_log.assert_awaited()


@pytest.mark.asyncio
async def test_execute_keeps_warning_result_level(
    runner_deps: tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_repo, run_repo, run_log_repo, log_repo = runner_deps

    async def fake_handler(ctx: object) -> TaskExecutionResult:
        return TaskExecutionResult(summary="warn", result_level="warning", metrics_value="1")

    runner = build_runner(
        task_registry=make_registry(**{"fetch-trains": fake_handler}),
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        log_repo=log_repo,
    )
    task_repo.find_by_id.return_value = make_task(task_type="fetch-trains")
    run_repo.update_run_status.return_value = make_run(
        status="completed",
        task_type="fetch-trains",
        result_level="warning",
    )

    await runner.execute(make_run(task_type="fetch-trains"))

    task_repo.apply_run_result.assert_any_await(
        1,
        11,
        "completed",
        result_level="warning",
        metrics_value="1",
        timing_value=pytest.approx(
            task_repo.apply_run_result.await_args.kwargs["timing_value"], rel=0.0
        ),
    )
    log_repo.write_log.assert_awaited()


@pytest.mark.asyncio
async def test_execute_marks_error_when_handler_raises(
    runner_deps: tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_repo, run_repo, run_log_repo, log_repo = runner_deps

    async def fake_handler(ctx: object) -> TaskExecutionResult:
        raise RuntimeError("boom")

    runner = build_runner(
        task_registry=make_registry(**{"fetch-trains": fake_handler}),
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        log_repo=log_repo,
    )
    task_repo.find_by_id.return_value = make_task(task_type="fetch-trains")
    run_repo.find_by_id.return_value = make_run(status="running", task_type="fetch-trains")
    run_repo.update_run_status.return_value = make_run(status="error", task_type="fetch-trains")

    await runner.execute(make_run(task_type="fetch-trains"))

    task_repo.apply_run_result.assert_any_await(
        1,
        11,
        "error",
        result_level="error",
        error_message="boom",
        timing_value=pytest.approx(
            task_repo.apply_run_result.await_args.kwargs["timing_value"], rel=0.0
        ),
    )
    run_log_repo.create_log.assert_awaited()
    log_repo.write_log.assert_awaited()
