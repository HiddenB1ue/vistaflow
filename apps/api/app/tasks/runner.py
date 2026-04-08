from __future__ import annotations

import asyncio
from time import monotonic

import asyncpg

from app.integrations.crawler.client import AbstractCrawlerClient
from app.integrations.geo.client import AbstractGeoClient
from app.models import TaskDefinition, TaskRun
from app.system.log_repository import LogRepository
from app.tasks.exceptions import TaskRunNotTerminable, TaskTypeNotImplemented, TaskTypeUnavailable
from app.tasks.execution import (
    TaskExecutionContext,
    TaskFrameworkPorts,
    TaskServiceAccess,
)
from app.tasks.progress import with_progress_state
from app.tasks.registry import TaskDefinitionRegistry, get_builtin_task_registry
from app.tasks.repository import TaskRepository, TaskRunLogRepository, TaskRunRepository
from app.tasks.runtime import TaskRuntimeRegistry

TASK_HANDLERS = {
    definition.type: definition.executor
    for definition in get_builtin_task_registry().all()
    if definition.executor is not None
}


class TaskRunner:
    def __init__(
        self,
        pool: asyncpg.Pool,
        task_repo: TaskRepository,
        run_repo: TaskRunRepository,
        run_log_repo: TaskRunLogRepository,
        log_repo: LogRepository,
        runtime_registry: TaskRuntimeRegistry,
        crawler_client: AbstractCrawlerClient,
        geo_client: AbstractGeoClient,
        task_registry: TaskDefinitionRegistry | None = None,
    ) -> None:
        self._pool = pool
        self._task_repo = task_repo
        self._run_repo = run_repo
        self._run_log_repo = run_log_repo
        self._log_repo = log_repo
        self._runtime_registry = runtime_registry
        self._task_registry = task_registry or get_builtin_task_registry()
        self._crawler_client = crawler_client
        self._geo_client = geo_client

    def schedule(self, task: TaskDefinition, run: TaskRun) -> None:
        background_task = asyncio.create_task(
            self.execute(task, run.id),
            name=f"task-run-{run.id}",
        )
        self._runtime_registry.register(run.id, task.id, background_task)

    async def terminate(self, run: TaskRun) -> TaskRun:
        active = self._runtime_registry.get_run(run.id)
        if active is None or active.task.done():
            raise TaskRunNotTerminable(run.id)
        active.task.cancel()
        await asyncio.gather(active.task, return_exceptions=True)
        refreshed = await self._run_repo.find_by_id(run.id)
        if refreshed is None:
            raise TaskRunNotTerminable(run.id)
        return refreshed

    async def execute(self, task: TaskDefinition, run_id: int) -> None:
        current_run = await self._run_repo.find_by_id(run_id)
        running_snapshot = with_progress_state(
            current_run.progress_snapshot if current_run is not None else None,
            task_type=task.type,
            stage="crawling",
            status="running",
        )
        await self._run_repo.update_run_status(
            run_id,
            "running",
            progress_snapshot=running_snapshot,
            set_started=True,
        )
        await self._task_repo.mark_task_running(task.id, run_id)
        await self._run_log_repo.create_log(run_id, "SYSTEM", f"任务 {task.name} 已开始执行")
        started_at = monotonic()

        try:
            definition = self._task_registry.get_optional(task.type)
            if definition is None:
                raise TaskTypeUnavailable(task.type)
            if not definition.implemented or definition.executor is None:
                raise TaskTypeNotImplemented(task.type)

            result = await definition.executor(
                TaskExecutionContext(
                    task=task,
                    run_id=run_id,
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
            timing_value = self._format_elapsed(started_at)
            completed_snapshot = with_progress_state(
                result.progress_snapshot,
                task_type=task.type,
                stage="completed",
                status="completed",
            )
            await self._run_repo.update_run_status(
                run_id,
                "completed",
                summary=result.summary,
                metrics_value=result.metrics_value,
                progress_snapshot=completed_snapshot,
                set_finished=True,
            )
            await self._task_repo.apply_run_result(
                task.id,
                run_id,
                "completed",
                metrics_value=result.metrics_value,
                timing_value=result.timing_value or timing_value,
            )
        except asyncio.CancelledError:
            await self._run_log_repo.create_log(
                run_id,
                "WARN",
                f"任务 {task.name} 已被管理员终止",
            )
            await self._log_repo.write_log(
                "WARN",
                f"任务 {task.name} 已被管理员终止",
                highlighted_terms=[task.type],
            )
            timing_value = self._format_elapsed(started_at)
            current_run = await self._run_repo.find_by_id(run_id)
            terminated_snapshot = with_progress_state(
                current_run.progress_snapshot if current_run is not None else None,
                task_type=task.type,
                stage="terminated",
                status="terminated",
            )
            await self._run_repo.update_run_status(
                run_id,
                "terminated",
                progress_snapshot=terminated_snapshot,
                error_message="执行已被管理员终止",
                termination_reason="管理员终止执行",
                set_finished=True,
            )
            await self._task_repo.apply_run_result(
                task.id,
                run_id,
                "terminated",
                error_message="执行已被管理员终止",
                timing_value=timing_value,
            )
        except Exception as exc:
            await self._run_log_repo.create_log(
                run_id,
                "ERROR",
                f"任务 {task.name} 执行失败: {exc}",
            )
            await self._log_repo.write_log(
                "ERROR",
                f"任务 {task.name} 执行失败: {exc}",
                highlighted_terms=[task.type],
            )
            timing_value = self._format_elapsed(started_at)
            current_run = await self._run_repo.find_by_id(run_id)
            error_snapshot = with_progress_state(
                current_run.progress_snapshot if current_run is not None else None,
                task_type=task.type,
                stage="error",
                status="error",
            )
            await self._run_repo.update_run_status(
                run_id,
                "error",
                progress_snapshot=error_snapshot,
                error_message=str(exc),
                set_finished=True,
            )
            await self._task_repo.apply_run_result(
                task.id,
                run_id,
                "error",
                error_message=str(exc),
                timing_value=timing_value,
            )
        finally:
            self._runtime_registry.unregister(run_id)
            latest = await self._run_repo.find_by_id(run_id)
            if latest is not None and latest.status == "completed":
                await self._log_repo.write_log(
                    "SUCCESS",
                    f"任务 {task.name} 执行完成",
                    highlighted_terms=[task.type],
                )

    @staticmethod
    def _format_elapsed(started_at: float) -> str:
        elapsed = monotonic() - started_at
        return f"{elapsed:.2f}s"
