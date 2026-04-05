from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.models import CrawlTask
from app.tasks.exceptions import TaskAlreadyRunning, TaskNotFound
from app.tasks.repository import TaskRepository
from app.tasks.schemas import TaskMetrics, TaskResponse, TaskTiming

if TYPE_CHECKING:
    from app.tasks.runner import TaskRunner


class TaskService:
    def __init__(self, repo: TaskRepository, runner: "TaskRunner") -> None:
        self._repo = repo
        self._runner = runner

    async def list_tasks(self) -> list[TaskResponse]:
        tasks = await self._repo.find_all()
        return [self._to_response(t) for t in tasks]

    async def trigger_task(self, task_id: int) -> TaskResponse:
        task = await self._repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFound(task_id)
        if task.status == "running":
            raise TaskAlreadyRunning(task_id)

        await self._repo.update_status(task_id, "running")
        updated = await self._repo.find_by_id(task_id)
        if updated is None:
            raise RuntimeError(f"Failed to reload task {task_id} after status update")

        asyncio.create_task(self._runner.execute(updated))

        return self._to_response(updated)

    @staticmethod
    def _to_response(task: CrawlTask) -> TaskResponse:
        return TaskResponse(
            id=task.id,
            name=task.name,
            type=task.type,
            typeLabel=task.type_label,
            status=task.status,
            description=task.description,
            cron=task.cron,
            metrics=TaskMetrics(label=task.metrics_label, value=task.metrics_value),
            timing=TaskTiming(label=task.timing_label, value=task.timing_value),
            errorMessage=task.error_message,
        )
