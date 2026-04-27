from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, field_validator

from app.models import TaskDefinition, TaskRun, TaskRunLog
from app.tasks.definition import (
    TaskCapabilityContract,
    TaskParamDefinition,
    TaskTypeDefinition,
)
from app.tasks.exceptions import (
    TaskAlreadyRunning,
    TaskCronUnsupported,
    TaskCronValidationError,
    TaskDeleteConflict,
    TaskDisabled,
    TaskNameConflict,
    TaskPayloadValidationError,
    TaskRunNotTerminable,
    TaskTypeNotImplemented,
    TaskTypeUnsupported,
    TaskUpdateConflict,
)
from app.tasks.registry import TaskDefinitionRegistry
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
        schedule_mode="manual",
        cron=None,
        payload=payload or {},
        status=status,
        latest_run_id=None,
        latest_run_status=None,
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
        task_name="站点同步",
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
        worker_id=None,
        heartbeat_at=None,
        cancel_requested=cancel_requested,
        cancel_requested_at=None,
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


class DemoPayload(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("code 不能为空")
        return cleaned.upper()


@pytest.fixture
def service() -> tuple[TaskService, AsyncMock, AsyncMock, AsyncMock]:
    task_repo = AsyncMock()
    run_repo = AsyncMock()
    run_log_repo = AsyncMock()
    return (
        TaskService(
            task_repo=task_repo,
            run_repo=run_repo,
            run_log_repo=run_log_repo,
        ),
        task_repo,
        run_repo,
        run_log_repo,
    )


@pytest.mark.asyncio
async def test_create_task_success(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task()

    result = await task_service.create_task(
        TaskCreateRequest(name="站点同步", type="fetch-station")
    )

    assert result.name == "站点同步"
    task_repo.create_task.assert_awaited_once()
    assert task_repo.create_task.await_args.kwargs["schedule_mode"] == "manual"
    assert task_repo.create_task.await_args.kwargs["next_run_at"] is None


@pytest.mark.asyncio
async def test_create_task_with_cron_sets_next_run_at(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task()

    await task_service.create_task(
        TaskCreateRequest(name="站点同步", type="fetch-station", cron="0 3 * * *")
    )

    assert task_repo.create_task.await_args.kwargs["schedule_mode"] == "cron"
    assert task_repo.create_task.await_args.kwargs["cron"] == "0 3 * * *"
    assert task_repo.create_task.await_args.kwargs["next_run_at"] is not None


@pytest.mark.asyncio
async def test_create_once_task_sets_next_run_at(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    run_at = datetime(2027, 4, 5, tzinfo=UTC)
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task()

    await task_service.create_task(
        TaskCreateRequest(
            name="One shot station sync",
            type="fetch-station",
            scheduleMode="once",
            runAt=run_at,
        )
    )

    assert task_repo.create_task.await_args.kwargs["schedule_mode"] == "once"
    assert task_repo.create_task.await_args.kwargs["cron"] is None
    assert task_repo.create_task.await_args.kwargs["next_run_at"] == run_at


@pytest.mark.asyncio
async def test_create_once_task_requires_future_run_at(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None

    with pytest.raises(TaskCronValidationError):
        await task_service.create_task(
            TaskCreateRequest(
                name="Past one shot station sync",
                type="fetch-station",
                scheduleMode="once",
                runAt=NOW - timedelta(minutes=1),
            )
        )


@pytest.mark.asyncio
async def test_create_task_rejects_invalid_cron(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None

    with pytest.raises(TaskCronValidationError):
        await task_service.create_task(
            TaskCreateRequest(name="站点同步", type="fetch-station", cron="bad cron")
        )


@pytest.mark.asyncio
async def test_create_task_rejects_cron_for_unsupported_type() -> None:
    task_repo = AsyncMock()
    run_repo = AsyncMock()
    run_log_repo = AsyncMock()
    task_repo.find_by_name.return_value = None
    registry = TaskDefinitionRegistry(
        (
            TaskTypeDefinition(
                type="demo-task",
                label="演示任务",
                description="不支持 Cron",
                implemented=True,
                capability=TaskCapabilityContract(supports_cron=False),
                executor=AsyncMock(),
            ),
        )
    )
    service = TaskService(
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        task_registry=registry,
    )

    with pytest.raises(TaskCronUnsupported):
        await service.create_task(
            TaskCreateRequest(name="Demo task", type="demo-task", cron="0 3 * * *")
        )


@pytest.mark.asyncio
async def test_create_once_task_rejects_unsupported_type() -> None:
    task_repo = AsyncMock()
    run_repo = AsyncMock()
    run_log_repo = AsyncMock()
    task_repo.find_by_name.return_value = None
    registry = TaskDefinitionRegistry(
        (
            TaskTypeDefinition(
                type="demo-task",
                label="Demo task",
                description="Does not support automatic scheduling",
                implemented=True,
                capability=TaskCapabilityContract(supports_cron=False),
                executor=AsyncMock(),
            ),
        )
    )
    service = TaskService(
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        task_registry=registry,
    )

    with pytest.raises(TaskCronUnsupported):
        await service.create_task(
            TaskCreateRequest(
                name="Demo task",
                type="demo-task",
                scheduleMode="once",
                runAt=NOW + timedelta(hours=1),
            )
        )


@pytest.mark.asyncio
async def test_create_railway_task_normalizes_payload(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
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
        "dateMode": "fixed",
        "date": "2026-04-05",
        "keyword": "G",
    }


@pytest.mark.asyncio
async def test_create_task_rejects_duplicate_name(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = make_task()

    with pytest.raises(TaskNameConflict):
        await task_service.create_task(
            TaskCreateRequest(name="站点同步", type="fetch-station")
        )


@pytest.mark.asyncio
async def test_create_task_rejects_unsupported_type(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, _, _, _ = service

    with pytest.raises(TaskTypeUnsupported):
        await task_service.create_task(
            TaskCreateRequest(name="站点同步", type="unknown-task")
        )


@pytest.mark.asyncio
async def test_create_railway_task_rejects_invalid_payload(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None

    with pytest.raises(TaskPayloadValidationError):
        await task_service.create_task(
            TaskCreateRequest(
                name="Broken task",
                type="fetch-train-stops",
                payload={"date": "bad-date", "keyword": " "},
            )
        )


@pytest.mark.asyncio
async def test_update_task_rejects_active_run(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task()
    run_repo.find_active_by_task.return_value = make_run(status="running")

    with pytest.raises(TaskUpdateConflict):
        await task_service.update_task(1, TaskUpdateRequest(description="new"))


@pytest.mark.asyncio
async def test_update_railway_task_normalizes_payload(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task(
        task_type="fetch-trains",
        type_label="爬取车次",
        payload={"date": "2026-04-05", "keyword": "G"},
    )
    task_repo.find_by_name.return_value = None
    task_repo.update_task.return_value = make_task(
        task_type="fetch-train-stops",
        type_label="爬取车次经停",
        payload={"date": "2026-04-06", "keyword": "G1"},
    )
    run_repo.find_active_by_task.return_value = None

    await task_service.update_task(
        1,
        TaskUpdateRequest(
            type="fetch-train-stops",
            payload={"date": "20260406", "keyword": " G1 "},
        ),
    )

    assert task_repo.update_task.await_args.kwargs["payload"] == {
        "dateMode": "fixed",
        "date": "2026-04-06",
        "keyword": "G1",
    }


@pytest.mark.asyncio
async def test_update_task_with_cron_sets_next_run_at(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task()
    task_repo.find_by_name.return_value = None
    task_repo.update_task.return_value = make_task()
    run_repo.find_active_by_task.return_value = None

    await task_service.update_task(1, TaskUpdateRequest(cron="*/15 * * * *"))

    assert task_repo.update_task.await_args.kwargs["schedule_mode"] == "cron"
    assert task_repo.update_task.await_args.kwargs["cron"] == "*/15 * * * *"
    assert task_repo.update_task.await_args.kwargs["next_run_at"] is not None


@pytest.mark.asyncio
async def test_update_task_can_clear_existing_cron(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task()
    task_repo.find_by_id.return_value.cron = "*/15 * * * *"
    task_repo.find_by_name.return_value = None
    task_repo.update_task.return_value = make_task()
    run_repo.find_active_by_task.return_value = None

    await task_service.update_task(1, TaskUpdateRequest(cron=""))

    assert task_repo.update_task.await_args.kwargs["cron"] is None
    assert task_repo.update_task.await_args.kwargs["next_run_at"] is None


@pytest.mark.asyncio
async def test_create_fetch_train_stops_task_allows_missing_keyword(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task(
        task_type="fetch-train-stops",
        type_label="爬取车次经停",
        payload={"date": "2026-04-05"},
    )

    await task_service.create_task(
        TaskCreateRequest(
            name="Stop sync all",
            type="fetch-train-stops",
            payload={"date": "20260405"},
        )
    )

    assert task_repo.create_task.await_args.kwargs["payload"] == {
        "dateMode": "fixed",
        "date": "2026-04-05",
    }


@pytest.mark.asyncio
async def test_create_fetch_train_runs_task_normalizes_keyword(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task(
        task_type="fetch-train-runs",
        type_label="获取某天运行的车次",
        payload={"date": "2026-04-05", "keyword": "G1"},
    )

    await task_service.create_task(
        TaskCreateRequest(
            name="Run sync",
            type="fetch-train-runs",
            payload={"date": "20260405", "keyword": " G1 "},
        )
    )

    assert task_repo.create_task.await_args.kwargs["payload"] == {
        "dateMode": "fixed",
        "date": "2026-04-05",
        "keyword": "G1",
    }


@pytest.mark.asyncio
async def test_create_fetch_train_runs_task_allows_missing_keyword(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task(
        task_type="fetch-train-runs",
        type_label="获取某天运行的车次",
        payload={"date": "2026-04-05"},
    )

    await task_service.create_task(
        TaskCreateRequest(
            name="Run sync all",
            type="fetch-train-runs",
            payload={"date": "20260405"},
        )
    )

    assert task_repo.create_task.await_args.kwargs["payload"] == {
        "dateMode": "fixed",
        "date": "2026-04-05",
    }


@pytest.mark.asyncio
async def test_create_fetch_station_geo_task_normalizes_address(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task(
        task_type="fetch-station-geo",
        type_label="站点坐标补全",
        payload={"address": "上海虹桥站"},
    )

    await task_service.create_task(
        TaskCreateRequest(
            name="Geo lookup",
            type="fetch-station-geo",
            payload={"address": " 上海虹桥站 "},
        )
    )

    assert task_repo.create_task.await_args.kwargs["payload"] == {
        "address": "上海虹桥站",
    }


@pytest.mark.asyncio
async def test_create_fetch_station_geo_task_allows_missing_address(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, _, _ = service
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task(
        task_type="fetch-station-geo",
        type_label="站点坐标补全",
        payload={},
    )

    await task_service.create_task(
        TaskCreateRequest(
            name="Geo batch",
            type="fetch-station-geo",
            payload={},
        )
    )

    assert task_repo.create_task.await_args.kwargs["payload"] == {}


@pytest.mark.asyncio
async def test_create_task_supports_registry_defined_custom_type() -> None:
    task_repo = AsyncMock()
    run_repo = AsyncMock()
    run_log_repo = AsyncMock()
    task_repo.find_by_name.return_value = None
    task_repo.create_task.return_value = make_task(
        task_type="demo-task",
        type_label="演示任务",
        payload={"code": "G123"},
    )
    registry = TaskDefinitionRegistry(
        (
            TaskTypeDefinition(
                type="demo-task",
                label="演示任务",
                description="通过注册表定义的示例任务",
                implemented=True,
                capability=TaskCapabilityContract(),
                param_schema=(
                    TaskParamDefinition(
                        key="code",
                        label="车次编码",
                        value_type="text",
                        required=True,
                        placeholder="例如 G123",
                        description="用于验证注册表自描述能力",
                    ),
                ),
                payload_model=DemoPayload,
                executor=AsyncMock(),
            ),
        )
    )
    service = TaskService(
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        task_registry=registry,
    )

    result = await service.create_task(
        TaskCreateRequest(
            name="Demo task",
            type="demo-task",
            payload={"code": " g123 "},
        )
    )

    assert result.type == "demo-task"
    assert result.typeLabel == "演示任务"
    assert task_repo.create_task.await_args.kwargs["payload"] == {"code": "G123"}


@pytest.mark.asyncio
async def test_list_task_types_reads_from_custom_registry() -> None:
    registry = TaskDefinitionRegistry(
        (
            TaskTypeDefinition(
                type="demo-task",
                label="演示任务",
                description="通过注册表定义的示例任务",
                implemented=True,
                capability=TaskCapabilityContract(supports_cron=False),
                param_schema=(
                    TaskParamDefinition(
                        key="code",
                        label="车次编码",
                        value_type="text",
                        required=True,
                        placeholder="例如 G123",
                        description="用于验证任务类型目录输出",
                    ),
                ),
                payload_model=DemoPayload,
                executor=AsyncMock(),
            ),
        )
    )
    service = TaskService(
        task_repo=AsyncMock(),
        run_repo=AsyncMock(),
        run_log_repo=AsyncMock(),
        task_registry=registry,
    )

    task_types = await service.list_task_types()

    assert [item.type for item in task_types] == ["demo-task"]
    assert task_types[0].label == "演示任务"
    assert task_types[0].supportsCron is False
    assert task_types[0].paramSchema[0].key == "code"


@pytest.mark.asyncio
async def test_delete_task_rejects_active_run(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task()
    run_repo.find_active_by_task.return_value = make_run(status="running")

    with pytest.raises(TaskDeleteConflict):
        await task_service.delete_task(1)


@pytest.mark.asyncio
async def test_trigger_task_success(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task()
    run_repo.find_active_by_task.return_value = None
    run_repo.create_run.return_value = make_run()
    run_repo.find_by_id.return_value = make_run()

    result = await task_service.trigger_task(1)

    assert result.taskId == 1
    assert result.status == "pending"
    task_repo.mark_task_pending.assert_awaited_once_with(1, 11)
    assert run_repo.create_run.await_args.kwargs["progress_snapshot"]["phase"] == "queued"


@pytest.mark.asyncio
async def test_trigger_task_normalizes_payload_before_queue(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task(
        task_type="fetch-trains",
        type_label="爬取车次",
        payload={"date": "20260405", "keyword": " G "},
    )
    run_repo.find_active_by_task.return_value = None
    run_repo.create_run.return_value = make_run(task_type="fetch-trains")
    run_repo.find_by_id.return_value = make_run(task_type="fetch-trains")

    await task_service.trigger_task(1)

    assert run_repo.create_run.await_args.kwargs["progress_snapshot"]["taskType"] == "fetch-trains"


@pytest.mark.asyncio
async def test_trigger_task_allows_fetch_trains_without_keyword(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task(
        task_type="fetch-trains",
        type_label="爬取车次",
        payload={"date": "20260405"},
    )
    run_repo.find_active_by_task.return_value = None
    run_repo.create_run.return_value = make_run(task_type="fetch-trains")
    run_repo.find_by_id.return_value = make_run(task_type="fetch-trains")

    result = await task_service.trigger_task(1)

    assert result.status == "pending"


@pytest.mark.asyncio
async def test_trigger_task_rejects_disabled_task(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task(enabled=False)
    run_repo.find_active_by_task.return_value = None

    with pytest.raises(TaskDisabled):
        await task_service.trigger_task(1)


@pytest.mark.asyncio
async def test_trigger_task_rejects_active_run(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task()
    run_repo.find_active_by_task.return_value = make_run(status="running")

    with pytest.raises(TaskAlreadyRunning):
        await task_service.trigger_task(1)


@pytest.mark.asyncio
async def test_trigger_task_rejects_unimplemented_type(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, task_repo, run_repo, _ = service
    task_repo.find_by_id.return_value = make_task(
        task_type="price",
        type_label="票价信息同步",
    )
    run_repo.find_active_by_task.return_value = None

    with pytest.raises(TaskTypeNotImplemented):
        await task_service.trigger_task(1)


@pytest.mark.asyncio
async def test_terminate_pending_run_marks_terminated(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, _, run_repo, _ = service
    run_repo.find_by_id.return_value = make_run(status="pending")
    run_repo.terminate_pending_run.return_value = make_run(
        status="terminated",
        result_level="error",
    )

    result = await task_service.terminate_run(11)

    assert result.status == "terminated"
    run_repo.terminate_pending_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_terminate_running_run_requests_cancellation(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, _, run_repo, _ = service
    run_repo.find_by_id.return_value = make_run(status="running")
    run_repo.request_cancellation.return_value = make_run(
        status="running",
        cancel_requested=True,
    )

    result = await task_service.terminate_run(11)

    assert result.status == "running"
    run_repo.request_cancellation.assert_awaited_once_with(11)


@pytest.mark.asyncio
async def test_terminate_run_rejects_completed(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, _, run_repo, _ = service
    run_repo.find_by_id.return_value = make_run(status="completed")

    with pytest.raises(TaskRunNotTerminable):
        await task_service.terminate_run(11)


@pytest.mark.asyncio
async def test_list_run_logs_returns_log_models(
    service: tuple[TaskService, AsyncMock, AsyncMock, AsyncMock],
) -> None:
    task_service, _, run_repo, run_log_repo = service
    run_repo.find_by_id.return_value = make_run()
    run_log_repo.list_by_run.return_value = [make_log()]

    logs = await task_service.list_run_logs(11)

    assert logs[0].runId == 11
    assert logs[0].message == "started"
