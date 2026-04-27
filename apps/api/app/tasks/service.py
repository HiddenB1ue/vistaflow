from __future__ import annotations

from datetime import datetime
from typing import cast

from app.models import TaskDefinition, TaskRun, TaskRunLog
from app.pagination import PaginatedResponse, create_paginated_response
from app.tasks.definition import TaskTypeDefinition
from app.tasks.exceptions import (
    TaskAlreadyRunning,
    TaskCronUnsupported,
    TaskCronValidationError,
    TaskDeleteConflict,
    TaskDisabled,
    TaskNameConflict,
    TaskNotFound,
    TaskRunNotFound,
    TaskRunNotTerminable,
    TaskTypeNotImplemented,
    TaskTypeUnavailable,
    TaskTypeUnsupported,
    TaskUpdateConflict,
)
from app.tasks.progress import build_progress_snapshot, with_progress_state
from app.tasks.registry import TaskDefinitionRegistry, get_builtin_task_registry
from app.tasks.repository import TaskRepository, TaskRunLogRepository, TaskRunRepository
from app.tasks.scheduler import next_scheduled_run_at, normalize_run_at, validate_cron_expression
from app.tasks.schemas import (
    TaskCreateRequest,
    TaskLatestRunResponse,
    TaskMetrics,
    TaskResponse,
    TaskRunLogResponse,
    TaskRunResponse,
    TaskScheduleMode,
    TaskTiming,
    TaskTypeResponse,
    TaskUpdateRequest,
    build_task_param_response,
)


class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,
        run_repo: TaskRunRepository,
        run_log_repo: TaskRunLogRepository,
        task_registry: TaskDefinitionRegistry | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._run_repo = run_repo
        self._run_log_repo = run_log_repo
        self._task_registry = task_registry or get_builtin_task_registry()

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
            for definition in self._task_registry.all()
        ]

    async def list_tasks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: str = "",
        status: str = "all",
    ) -> PaginatedResponse[TaskResponse]:
        """List tasks with pagination, filtering, and search."""
        tasks, total = await self._task_repo.find_all_paginated(
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
        )
        items = [self._to_task_response(task) for task in tasks]
        return create_paginated_response(items, page, page_size, total)

    async def get_task(self, task_id: int) -> TaskResponse:
        task = await self._require_task(task_id)
        return self._to_task_response(task)

    async def create_task(self, payload: TaskCreateRequest) -> TaskResponse:
        definition = self._require_task_type_definition(payload.type)
        await self._ensure_name_available(payload.name)
        normalized_payload = self._task_registry.normalize_payload(payload.type, payload.payload)
        schedule_mode = self._resolve_create_schedule_mode(payload)
        cron, next_run_at = self._normalize_schedule_for_definition(
            definition,
            schedule_mode=schedule_mode,
            cron=payload.cron,
            run_at=payload.runAt,
        )
        task = await self._task_repo.create_task(
            name=payload.name,
            task_type=payload.type,
            type_label=definition.label,
            description=payload.description,
            enabled=payload.enabled,
            schedule_mode=schedule_mode,
            cron=cron,
            next_run_at=next_run_at,
            payload=normalized_payload,
        )
        return self._to_task_response(task)

    async def update_task(self, task_id: int, payload: TaskUpdateRequest) -> TaskResponse:
        existing = await self._require_task(task_id)
        active = await self._run_repo.find_active_by_task(task_id)
        if active is not None and not self._is_enabled_only_update(payload):
            raise TaskUpdateConflict(task_id)

        task_type = payload.type or existing.type
        definition = self._require_task_type_definition(task_type)
        name = payload.name or existing.name
        await self._ensure_name_available(name, exclude_task_id=task_id)
        candidate_payload = payload.payload if payload.payload is not None else existing.payload
        normalized_payload = self._task_registry.normalize_payload(task_type, candidate_payload)
        schedule_mode = self._resolve_update_schedule_mode(existing, payload)
        cron_value = (
            (payload.cron if "cron" in payload.model_fields_set else existing.cron)
            if schedule_mode == "cron"
            else None
        )
        run_at_value = (
            (payload.runAt if "runAt" in payload.model_fields_set else existing.next_run_at)
            if schedule_mode == "once"
            else None
        )
        cron, next_run_at = self._normalize_schedule_for_definition(
            definition,
            schedule_mode=schedule_mode,
            cron=cron_value,
            run_at=run_at_value,
        )
        enabled = payload.enabled if payload.enabled is not None else existing.enabled
        if not enabled:
            next_run_at = None

        updated = await self._task_repo.update_task(
            task_id,
            name=name,
            task_type=task_type,
            type_label=definition.label,
            description=(
                payload.description if payload.description is not None else existing.description
            ),
            enabled=enabled,
            schedule_mode=schedule_mode,
            cron=cron,
            next_run_at=next_run_at,
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
        definition = self._require_task_type_definition(task.type)
        active = await self._run_repo.find_active_by_task(task_id)
        if active is not None:
            raise TaskAlreadyRunning(task_id)
        if not task.enabled:
            raise TaskDisabled(task_id)
        if not definition.implemented or not definition.capability.can_run:
            raise TaskTypeNotImplemented(task.type)

        self._task_registry.normalize_payload(task.type, task.payload)
        progress_snapshot = build_progress_snapshot(
            task.type,
            phase="queued",
            status="pending",
        )
        run = await self._run_repo.create_run(
            task_id=task_id,
            progress_snapshot=progress_snapshot,
        )
        await self._task_repo.mark_task_pending(task_id, run.id)
        latest_run = await self._require_run(run.id)
        return self._to_run_response(latest_run)

    async def terminate_run(self, run_id: int) -> TaskRunResponse:
        run = await self._require_run(run_id)
        definition = self._require_task_type_definition(run.task_type)
        if not definition.capability.can_terminate:
            raise TaskRunNotTerminable(run_id)

        if run.status == "pending":
            terminated = await self._run_repo.terminate_pending_run(
                run_id,
                termination_reason="管理员终止执行",
                error_message="执行已被管理员终止",
            )
            if terminated.progress_snapshot is not None:
                terminated = await self._run_repo.update_progress_snapshot(
                    run_id,
                    with_progress_state(
                        terminated.progress_snapshot,
                        task_type=run.task_type,
                        phase="terminated",
                        status="terminated",
                    ),
                )
            await self._task_repo.apply_run_result(
                run.task_id,
                run.id,
                "terminated",
                result_level="error",
                error_message="执行已被管理员终止",
            )
            return self._to_run_response(terminated)

        if run.status == "running":
            cancellation_requested = await self._run_repo.request_cancellation(run_id)
            return self._to_run_response(cancellation_requested)

        raise TaskRunNotTerminable(run_id)

    async def list_runs(
        self,
        task_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[TaskRunResponse]:
        """List task runs with pagination."""
        await self._require_task(task_id)
        runs, total = await self._run_repo.list_by_task_paginated(
            task_id,
            page=page,
            page_size=page_size,
        )
        items = [self._to_run_response(run) for run in runs]
        return create_paginated_response(items, page, page_size, total)

    async def get_run(self, run_id: int) -> TaskRunResponse:
        run = await self._require_run(run_id)
        return self._to_run_response(run)

    async def list_run_logs(self, run_id: int) -> list[TaskRunLogResponse]:
        await self._require_run(run_id)
        logs = await self._run_log_repo.list_by_run(run_id)
        return [self._to_run_log_response(log) for log in logs]

    async def list_run_logs_paginated(
        self,
        run_id: int,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> PaginatedResponse[TaskRunLogResponse]:
        """List task run logs with pagination."""
        await self._require_run(run_id)
        logs, total = await self._run_log_repo.list_by_run_paginated(
            run_id,
            page=page,
            page_size=page_size,
        )
        items = [self._to_run_log_response(log) for log in logs]
        return create_paginated_response(items, page, page_size, total)

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

    def _require_task_type_definition(self, task_type: str) -> TaskTypeDefinition:
        definition = self._task_registry.get_optional(task_type)
        if definition is None:
            raise TaskTypeUnsupported(task_type)
        if definition.executor is None and definition.implemented:
            raise TaskTypeUnavailable(task_type)
        return definition

    @staticmethod
    def _resolve_create_schedule_mode(payload: TaskCreateRequest) -> TaskScheduleMode:
        if payload.scheduleMode is not None:
            return payload.scheduleMode
        if payload.cron is not None:
            return "cron"
        return "manual"

    @staticmethod
    def _resolve_update_schedule_mode(
        existing: TaskDefinition,
        payload: TaskUpdateRequest,
    ) -> TaskScheduleMode:
        if payload.scheduleMode is not None:
            return payload.scheduleMode
        if "cron" in payload.model_fields_set:
            return "cron" if payload.cron is not None else "manual"
        existing_mode = existing.schedule_mode
        if existing_mode in {"manual", "once", "cron"}:
            return existing_mode  # type: ignore[return-value]
        return "cron" if existing.cron is not None else "manual"

    @staticmethod
    def _is_enabled_only_update(payload: TaskUpdateRequest) -> bool:
        return payload.model_fields_set == {"enabled"}

    @staticmethod
    def _normalize_schedule_for_definition(
        definition: TaskTypeDefinition,
        *,
        schedule_mode: TaskScheduleMode,
        cron: str | None,
        run_at: datetime | None,
    ) -> tuple[str | None, datetime | None]:
        if schedule_mode == "cron" and cron is None and run_at is not None:
            raise TaskCronValidationError("重复执行不能使用一次性执行时间")
        if schedule_mode == "once" and cron is not None:
            raise TaskCronValidationError("执行一次不能填写 Cron 表达式")
        if schedule_mode in {"once", "cron"} and not definition.supports_cron:
            raise TaskCronUnsupported(definition.type)
        if schedule_mode == "manual":
            return None, None
        if schedule_mode == "once":
            return None, normalize_run_at(run_at)
        if cron is None:
            raise TaskCronValidationError("重复执行需要填写 Cron 表达式")
        normalized = validate_cron_expression(cron)
        return normalized, next_scheduled_run_at(normalized)

    @staticmethod
    def _to_task_response(task: TaskDefinition) -> TaskResponse:
        latest_run = None
        if task.latest_run_id is not None and task.latest_run_status is not None:
            latest_run = TaskLatestRunResponse(
                id=task.latest_run_id,
                status=task.latest_run_status,
                resultLevel=task.latest_result_level,
                startedAt=task.latest_run_started_at,
                finishedAt=task.latest_run_finished_at,
                errorMessage=task.latest_error_message,
            )
        schedule_mode: TaskScheduleMode = (
            cast(TaskScheduleMode, task.schedule_mode)
            if task.schedule_mode in {"manual", "once", "cron"}
            else ("cron" if task.cron is not None else "manual")
        )
        return TaskResponse(
            id=task.id,
            name=task.name,
            type=task.type,
            typeLabel=task.type_label,
            status=task.status,
            description=task.description,
            enabled=task.enabled,
            scheduleMode=schedule_mode,
            cron=task.cron,
            runAt=task.next_run_at if schedule_mode == "once" else None,
            nextRunAt=task.next_run_at,
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
            resultLevel=run.result_level,
            metricsValue=run.metrics_value,
            progressSnapshot=run.progress_snapshot,
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
