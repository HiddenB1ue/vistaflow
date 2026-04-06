from __future__ import annotations

from dataclasses import replace

from app.models import TaskDefinition, TaskRun, TaskRunLog
from app.tasks.constants import (
    TASK_TYPES,
    get_task_type_definition,
    get_task_type_label,
    is_implemented_task_type,
    is_supported_task_type,
)
from app.tasks.exceptions import (
    TaskAlreadyRunning,
    TaskDeleteConflict,
    TaskDisabled,
    TaskNameConflict,
    TaskNotFound,
    TaskRunNotFound,
    TaskTypeNotImplemented,
    TaskTypeUnsupported,
    TaskUpdateConflict,
)
from app.tasks.repository import TaskRepository, TaskRunLogRepository, TaskRunRepository
from app.tasks.runner import TaskRunner
from app.tasks.schemas import (
    TaskCreateRequest,
    TaskLatestRunResponse,
    TaskMetrics,
    TaskResponse,
    TaskRunLogResponse,
    TaskRunResponse,
    TaskTiming,
    TaskTypeResponse,
    TaskUpdateRequest,
    build_task_param_response,
    normalize_task_payload,
)


class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,
        run_repo: TaskRunRepository,
        run_log_repo: TaskRunLogRepository,
        runner: TaskRunner,
    ) -> None:
        self._task_repo = task_repo
        self._run_repo = run_repo
        self._run_log_repo = run_log_repo
        self._runner = runner

    async def list_task_types(self) -> list[TaskTypeResponse]:
        return [
            TaskTypeResponse(
                type=definition.type,
                label=definition.label,
                description=definition.description,
                implemented=definition.implemented,
                supportsCron=definition.supports_cron,
                paramSchema=[build_task_param_response(param) for param in definition.param_schema],
            )
            for definition in TASK_TYPES.values()
        ]

    async def list_tasks(self) -> list[TaskResponse]:
        tasks = await self._task_repo.find_all()
        return [self._to_task_response(task) for task in tasks]

    async def get_task(self, task_id: int) -> TaskResponse:
        task = await self._require_task(task_id)
        return self._to_task_response(task)

    async def create_task(self, payload: TaskCreateRequest) -> TaskResponse:
        self._validate_task_type(payload.type)
        await self._ensure_name_available(payload.name)
        normalized_payload = normalize_task_payload(payload.type, payload.payload)
        task = await self._task_repo.create_task(
            name=payload.name,
            task_type=payload.type,
            type_label=get_task_type_label(payload.type),
            description=payload.description,
            enabled=payload.enabled,
            cron=payload.cron,
            payload=normalized_payload,
        )
        return self._to_task_response(task)

    async def update_task(self, task_id: int, payload: TaskUpdateRequest) -> TaskResponse:
        existing = await self._require_task(task_id)
        active = await self._run_repo.find_active_by_task(task_id)
        if active is not None:
            raise TaskUpdateConflict(task_id)

        task_type = payload.type or existing.type
        self._validate_task_type(task_type)
        name = payload.name or existing.name
        await self._ensure_name_available(name, exclude_task_id=task_id)
        candidate_payload = payload.payload if payload.payload is not None else existing.payload
        normalized_payload = normalize_task_payload(task_type, candidate_payload)

        updated = await self._task_repo.update_task(
            task_id,
            name=name,
            task_type=task_type,
            type_label=get_task_type_label(task_type),
            description=(
                payload.description if payload.description is not None else existing.description
            ),
            enabled=payload.enabled if payload.enabled is not None else existing.enabled,
            cron=payload.cron if payload.cron is not None else existing.cron,
            payload=normalized_payload,
        )
        return self._to_task_response(updated)

    async def delete_task(self, task_id: int) -> None:
        await self._require_task(task_id)
        active = await self._run_repo.find_active_by_task(task_id)
        if active is not None:
            raise TaskDeleteConflict(task_id)
        await self._task_repo.delete_task(task_id)

    async def trigger_task(self, task_id: int) -> TaskRunResponse:
        task = await self._require_task(task_id)
        active = await self._run_repo.find_active_by_task(task_id)
        if active is not None:
            raise TaskAlreadyRunning(task_id)
        if not task.enabled:
            raise TaskDisabled(task_id)
        if not is_implemented_task_type(task.type):
            raise TaskTypeNotImplemented(task.type)

        normalized_payload = normalize_task_payload(task.type, task.payload)
        run = await self._run_repo.create_run(task_id=task_id)
        await self._task_repo.mark_task_running(task_id, run.id)
        scheduled_task = replace(task, payload=normalized_payload)
        self._runner.schedule(scheduled_task, run)
        latest_run = await self._require_run(run.id)
        return self._to_run_response(latest_run)

    async def terminate_run(self, run_id: int) -> TaskRunResponse:
        run = await self._require_run(run_id)
        terminated = await self._runner.terminate(run)
        return self._to_run_response(terminated)

    async def list_runs(self, task_id: int) -> list[TaskRunResponse]:
        await self._require_task(task_id)
        runs = await self._run_repo.list_by_task(task_id)
        return [self._to_run_response(run) for run in runs]

    async def get_run(self, run_id: int) -> TaskRunResponse:
        run = await self._require_run(run_id)
        return self._to_run_response(run)

    async def list_run_logs(self, run_id: int) -> list[TaskRunLogResponse]:
        await self._require_run(run_id)
        logs = await self._run_log_repo.list_by_run(run_id)
        return [self._to_run_log_response(log) for log in logs]

    async def _require_task(self, task_id: int) -> TaskDefinition:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFound(task_id)
        return task

    async def _require_run(self, run_id: int) -> TaskRun:
        run = await self._run_repo.find_by_id(run_id)
        if run is None:
            raise TaskRunNotFound(run_id)
        return run

    async def _ensure_name_available(
        self, name: str, *, exclude_task_id: int | None = None
    ) -> None:
        existing = await self._task_repo.find_by_name(name)
        if existing is None:
            return
        if exclude_task_id is not None and existing.id == exclude_task_id:
            return
        raise TaskNameConflict(name)

    @staticmethod
    def _validate_task_type(task_type: str) -> None:
        if not is_supported_task_type(task_type):
            raise TaskTypeUnsupported(task_type)
        definition = get_task_type_definition(task_type)
        if definition is None:
            raise TaskTypeUnsupported(task_type)

    @staticmethod
    def _to_task_response(task: TaskDefinition) -> TaskResponse:
        latest_run = None
        if task.latest_run_id is not None and task.latest_run_status is not None:
            latest_run = TaskLatestRunResponse(
                id=task.latest_run_id,
                status=task.latest_run_status,
                startedAt=task.latest_run_started_at,
                finishedAt=task.latest_run_finished_at,
                errorMessage=task.latest_error_message,
            )
        return TaskResponse(
            id=task.id,
            name=task.name,
            type=task.type,
            typeLabel=task.type_label,
            status=task.status,
            description=task.description,
            enabled=task.enabled,
            cron=task.cron,
            payload=task.payload,
            metrics=TaskMetrics(label=task.metrics_label, value=task.metrics_value),
            timing=TaskTiming(label=task.timing_label, value=task.timing_value),
            errorMessage=task.error_message,
            latestRun=latest_run,
        )

    @staticmethod
    def _to_run_response(run: TaskRun) -> TaskRunResponse:
        return TaskRunResponse(
            id=run.id,
            taskId=run.task_id,
            taskName=run.task_name,
            taskType=run.task_type,
            triggerMode=run.trigger_mode,
            status=run.status,
            requestedBy=run.requested_by,
            summary=run.summary,
            metricsValue=run.metrics_value,
            errorMessage=run.error_message,
            terminationReason=run.termination_reason,
            startedAt=run.started_at,
            finishedAt=run.finished_at,
            createdAt=run.created_at,
            updatedAt=run.updated_at,
        )

    @staticmethod
    def _to_run_log_response(log: TaskRunLog) -> TaskRunLogResponse:
        return TaskRunLogResponse(
            id=log.id,
            runId=log.run_id,
            severity=log.severity,
            message=log.message,
            createdAt=log.created_at,
        )
