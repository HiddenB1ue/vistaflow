from __future__ import annotations

import asyncio
from dataclasses import replace
from time import monotonic

import asyncpg

from app.integrations.crawler.client import AbstractCrawlerClient
from app.integrations.geo.client import AbstractGeoClient
from app.models import TaskRun
from app.system.log_repository import LogRepository
from app.tasks.exceptions import (
    TaskCancellationRequested,
    TaskTypeNotImplemented,
    TaskTypeUnavailable,
)
from app.tasks.execution import TaskExecutionContext, TaskFrameworkPorts, TaskServiceAccess
from app.tasks.progress import with_progress_state
from app.tasks.registry import TaskDefinitionRegistry, get_builtin_task_registry
from app.tasks.repository import TaskRepository, TaskRunLogRepository, TaskRunRepository


class TaskRunner:
    def __init__(
        self,
        pool: asyncpg.Pool,
        task_repo: TaskRepository,
        run_repo: TaskRunRepository,
        run_log_repo: TaskRunLogRepository,
        log_repo: LogRepository,
        crawler_client: AbstractCrawlerClient,
        geo_client: AbstractGeoClient,
        worker_id: str,
        heartbeat_interval_seconds: float,
        task_registry: TaskDefinitionRegistry | None = None,
    ) -> None:
        self._pool = pool
        self._task_repo = task_repo
        self._run_repo = run_repo
        self._run_log_repo = run_log_repo
        self._log_repo = log_repo
        self._task_registry = task_registry or get_builtin_task_registry()
        self._crawler_client = crawler_client
        self._geo_client = geo_client
        self._worker_id = worker_id
        self._heartbeat_interval_seconds = heartbeat_interval_seconds

    async def execute(self, run: TaskRun) -> TaskRun:
        task = await self._task_repo.find_by_id(run.task_id)
        task_name = task.name if task is not None else run.task_name
        task_type = task.type if task is not None else run.task_type
        heartbeat_task: asyncio.Task[None] | None = None
        started_at = monotonic()

        try:
            if task is None:
                raise TaskTypeUnavailable(run.task_type)

            definition = self._task_registry.get_optional(task.type)
            if definition is None:
                raise TaskTypeUnavailable(task.type)
            if not definition.implemented or definition.executor is None:
                raise TaskTypeNotImplemented(task.type)

            normalized_task = replace(
                task,
                payload=self._task_registry.normalize_payload(task.type, task.payload),
            )
            running_snapshot = with_progress_state(
                run.progress_snapshot,
                task_type=task.type,
                phase="processing",
                status="running",
            )
            await self._run_repo.update_run_status(
                run.id,
                "running",
                progress_snapshot=running_snapshot,
                worker_id=self._worker_id,
                set_started=True,
            )
            await self._task_repo.mark_task_running(task.id, run.id)
            await self._run_log_repo.create_log(run.id, "SYSTEM", f"任务 {task.name} 已开始执行")
            heartbeat_task = asyncio.create_task(self._heartbeat_loop(run.id))

            result = await definition.executor(
                TaskExecutionContext(
                    task=normalized_task,
                    run_id=run.id,
                    framework=TaskFrameworkPorts(
                        pool=self._pool,
                        run_repo=self._run_repo,
                        run_log_repo=self._run_log_repo,
                        log_repo=self._log_repo,
                    ),
                    service_access=TaskServiceAccess(
                        crawler_client=self._crawler_client,
                        geo_client=self._geo_client,
                    ),
                )
            )
            timing_value = result.timing_value or self._format_elapsed(started_at)
            completed_snapshot = with_progress_state(
                result.progress_snapshot,
                task_type=task.type,
                phase="completed",
                status="completed",
            )
            updated = await self._run_repo.update_run_status(
                run.id,
                "completed",
                summary=result.summary,
                result_level=result.result_level,
                metrics_value=result.metrics_value,
                progress_snapshot=completed_snapshot,
                set_finished=True,
            )
            await self._task_repo.apply_run_result(
                task.id,
                run.id,
                "completed",
                result_level=result.result_level,
                metrics_value=result.metrics_value,
                timing_value=timing_value,
            )
            completion_severity = "WARN" if result.result_level == "warning" else "SUCCESS"
            completion_message = (
                f"任务 {task_name} 执行完成，存在告警"
                if result.result_level == "warning"
                else f"任务 {task_name} 执行完成"
            )
            await self._log_repo.write_log(
                completion_severity,
                completion_message,
                highlighted_terms=[task_type],
            )
            return updated
        except TaskCancellationRequested:
            await self._run_log_repo.create_log(run.id, "WARN", f"任务 {task_name} 已被管理员终止")
            await self._log_repo.write_log(
                "WARN",
                f"任务 {task_name} 已被管理员终止",
                highlighted_terms=[task_type],
            )
            timing_value = self._format_elapsed(started_at)
            current_run = await self._run_repo.find_by_id(run.id)
            terminated_snapshot = with_progress_state(
                current_run.progress_snapshot if current_run is not None else None,
                task_type=task_type,
                phase="terminated",
                status="terminated",
            )
            updated = await self._run_repo.update_run_status(
                run.id,
                "terminated",
                result_level="error",
                progress_snapshot=terminated_snapshot,
                error_message="执行已被管理员终止",
                termination_reason="管理员终止执行",
                set_finished=True,
            )
            await self._task_repo.apply_run_result(
                run.task_id,
                run.id,
                "terminated",
                result_level="error",
                error_message="执行已被管理员终止",
                timing_value=timing_value,
            )
            return updated
        except Exception as exc:
            await self._run_log_repo.create_log(run.id, "ERROR", f"任务 {task_name} 执行失败: {exc}")
            await self._log_repo.write_log(
                "ERROR",
                f"任务 {task_name} 执行失败: {exc}",
                highlighted_terms=[task_type],
            )
            timing_value = self._format_elapsed(started_at)
            current_run = await self._run_repo.find_by_id(run.id)
            error_snapshot = with_progress_state(
                current_run.progress_snapshot if current_run is not None else None,
                task_type=task_type,
                phase="error",
                status="error",
            )
            updated = await self._run_repo.update_run_status(
                run.id,
                "error",
                result_level="error",
                progress_snapshot=error_snapshot,
                error_message=str(exc),
                set_finished=True,
            )
            await self._task_repo.apply_run_result(
                run.task_id,
                run.id,
                "error",
                result_level="error",
                error_message=str(exc),
                timing_value=timing_value,
            )
            return updated
        finally:
            if heartbeat_task is not None:
                heartbeat_task.cancel()
                await asyncio.gather(heartbeat_task, return_exceptions=True)

    async def _heartbeat_loop(self, run_id: int) -> None:
        try:
            while True:
                await asyncio.sleep(self._heartbeat_interval_seconds)
                await self._run_repo.heartbeat(run_id, self._worker_id)
        except asyncio.CancelledError:
            return

    @staticmethod
    def _format_elapsed(started_at: float) -> str:
        return f"{monotonic() - started_at:.2f}s"
