from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import TaskDefinition, TaskRun, TaskRunLog
from app.tasks.exceptions import (
    TaskAlreadyRunning,
    TaskDeleteConflict,
    TaskDisabled,
    TaskNameConflict,
    TaskPayloadValidationError,
    TaskTypeNotImplemented,
    TaskTypeUnsupported,
    TaskUpdateConflict,
)
from app.tasks.schemas import TaskCreateRequest, TaskUpdateRequest
from app.tasks.service import TaskService

NOW = datetime(2026, 4, 5, tzinfo=UTC)


def make_task(
    *,
    task_id: int = 1,
    name: str = "站点同步",
    task_type: str = "fetch-station",
    type_label: str = "站点主数据同步",
    enabled: bool = True,
    status: str = "idle",
    payload: dict[str, object] | None = None,
) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        name=name,
        type=task_type,
        type_label=type_label,
        description="同步站点",
        enabled=enabled,
        cron=None,
        payload=payload or {},
        status=status,
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


def make_run(*, status: str = "pending") -> TaskRun:
    return TaskRun(
        id=11,
        task_id=1,
        task_name="站点同步",
        task_type="fetch-station",
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


def make_log() -> TaskRunLog:
    return TaskRunLog(
        id=1,
        run_id=11,
        severity="INFO",
        message="started",
        created_at=NOW,
    )


@pytest.fixture
def service() -> tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock]:
    task_repo = AsyncMock()
    run_repo = AsyncMock()
    run_log_repo = AsyncMock()
    runner = MagicMock()
    runner.schedule = MagicMock()
    runner.terminate = AsyncMock()
    return (
        TaskService(
            task_repo=task_repo,
            run_repo=run_repo,
            run_log_repo=run_log_repo,
            runner=runner,
        ),
        task_repo,
        run_repo,
        run_log_repo,
        runner,
    )


@pytest.mark.asyncio
async def test_create_task_success(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, _, _, _ = service
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task()

    result = await task_service.create_task(
        TaskCreateRequest(name="站点同步", type="fetch-station")
    )

    assert result.name == "站点同步"
    task_repo.create_task.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_railway_task_normalizes_payload(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, _, _, _ = service
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task(
        task_type="fetch-trains",
        type_label="爬取车次",
        payload={"date": "2026-04-05", "keyword": "G"},
    )

    await task_service.create_task(
        TaskCreateRequest(
            name="Train sync",
            type="fetch-trains",
            payload={"date": "20260405", "keyword": " G "},
        )
    )

    assert task_repo.create_task.await_args.kwargs["payload"] == {
        "date": "2026-04-05",
        "keyword": "G",
    }


@pytest.mark.asyncio
async def test_create_task_rejects_duplicate_name(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, _, _, _ = service
    task_repo.find_by_name.return_value = make_task()

    with pytest.raises(TaskNameConflict):
        await task_service.create_task(
            TaskCreateRequest(name="站点同步", type="fetch-station")
        )


@pytest.mark.asyncio
async def test_create_task_rejects_unsupported_type(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, _, _, _, _ = service

    with pytest.raises(TaskTypeUnsupported):
        await task_service.create_task(
            TaskCreateRequest(name="站点同步", type="unknown-task")
        )


@pytest.mark.asyncio
async def test_create_railway_task_rejects_invalid_payload(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, _, _, _ = service
    task_repo.find_by_name.return_value = None

    with pytest.raises(TaskPayloadValidationError):
        await task_service.create_task(
            TaskCreateRequest(
                name="Broken task",
                type="fetch-train-stops",
                payload={"date": "bad-date", "train_code": " "},
            )
        )


@pytest.mark.asyncio
async def test_update_task_rejects_active_run(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, run_repo, _, _ = service
    task_repo.find_by_id.return_value = make_task()
    run_repo.find_active_by_task.return_value = make_run(status="running")

    with pytest.raises(TaskUpdateConflict):
        await task_service.update_task(1, TaskUpdateRequest(description="new"))


@pytest.mark.asyncio
async def test_update_railway_task_normalizes_payload(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, run_repo, _, _ = service
    task_repo.find_by_id.return_value = make_task(
        task_type="fetch-trains",
        type_label="爬取车次",
        payload={"date": "2026-04-05", "keyword": "G"},
    )
    task_repo.find_by_name.return_value = None
    task_repo.update_task.return_value = make_task(
        task_type="fetch-train-stops",
        type_label="爬取车次经停",
        payload={"date": "2026-04-06", "train_code": "G1"},
    )
    run_repo.find_active_by_task.return_value = None

    await task_service.update_task(
        1,
        TaskUpdateRequest(
            type="fetch-train-stops",
            payload={"date": "20260406", "train_code": " G1 "},
        ),
    )

    assert task_repo.update_task.await_args.kwargs["payload"] == {
        "date": "2026-04-06",
        "train_code": "G1",
    }


@pytest.mark.asyncio
async def test_delete_task_rejects_active_run(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, run_repo, _, _ = service
    task_repo.find_by_id.return_value = make_task()
    run_repo.find_active_by_task.return_value = make_run(status="running")

    with pytest.raises(TaskDeleteConflict):
        await task_service.delete_task(1)


@pytest.mark.asyncio
async def test_trigger_task_success(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, run_repo, _, runner = service
    task = make_task()
    task_repo.find_by_id.return_value = task
    run_repo.find_active_by_task.return_value = None
    run_repo.create_run.return_value = make_run()
    run_repo.find_by_id.return_value = make_run(status="running")

    result = await task_service.trigger_task(1)

    assert result.taskId == 1
    task_repo.mark_task_running.assert_awaited_once_with(1, 11)
    runner.schedule.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_task_normalizes_railway_payload_before_schedule(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, run_repo, _, runner = service
    task_repo.find_by_id.return_value = make_task(
        task_type="fetch-trains",
        type_label="爬取车次",
        payload={"date": "20260405", "keyword": " G "},
    )
    run_repo.find_active_by_task.return_value = None
    run_repo.create_run.return_value = make_run()
    run_repo.find_by_id.return_value = make_run(status="running")

    await task_service.trigger_task(1)

    scheduled_task = runner.schedule.call_args.args[0]
    assert scheduled_task.payload == {"date": "2026-04-05", "keyword": "G"}


@pytest.mark.asyncio
async def test_trigger_task_rejects_disabled_task(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, run_repo, _, _ = service
    task_repo.find_by_id.return_value = make_task(enabled=False)
    run_repo.find_active_by_task.return_value = None

    with pytest.raises(TaskDisabled):
        await task_service.trigger_task(1)


@pytest.mark.asyncio
async def test_trigger_task_rejects_active_run(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, run_repo, _, _ = service
    task_repo.find_by_id.return_value = make_task()
    run_repo.find_active_by_task.return_value = make_run(status="running")

    with pytest.raises(TaskAlreadyRunning):
        await task_service.trigger_task(1)


@pytest.mark.asyncio
async def test_trigger_task_rejects_unimplemented_type(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, MagicMock],
) -> None:
    task_service, task_repo, run_repo, _, _ = service
    task_repo.find_by_id.return_value = make_task(
        task_type="price",
        type_label="票价信息同步",
    )
    run_repo.find_active_by_task.return_value = None

    with pytest.raises(TaskTypeNotImplemented):
        await task_service.trigger_task(1)


@pytest.mark.asyncio
async def test_list_run_logs_returns_log_models(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, _, run_repo, run_log_repo, _ = service
    run_repo.find_by_id.return_value = make_run()
    run_log_repo.list_by_run.return_value = [make_log()]

    logs = await task_service.list_run_logs(11)

    assert logs[0].runId == 11
    assert logs[0].message == "started"
