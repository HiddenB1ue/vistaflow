from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Request

from app.railway.dependencies import DbPool
from app.tasks.registry import TaskDefinitionRegistry
from app.tasks.repository import TaskRepository, TaskRunLogRepository, TaskRunRepository
from app.tasks.service import TaskService


def get_task_registry(request: Request) -> TaskDefinitionRegistry:
    return cast(TaskDefinitionRegistry, request.app.state.task_registry)


TaskRegistryDep = Annotated[TaskDefinitionRegistry, Depends(get_task_registry)]


def get_task_service(
    pool: DbPool,
    task_registry: TaskRegistryDep,
) -> TaskService:
    task_repo = TaskRepository(pool)
    run_repo = TaskRunRepository(pool)
    run_log_repo = TaskRunLogRepository(pool)
    return TaskService(
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        task_registry=task_registry,
    )


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
