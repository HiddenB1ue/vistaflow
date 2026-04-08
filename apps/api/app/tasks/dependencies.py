from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Request

from app.railway.dependencies import DbPool
from app.system.log_repository import LogRepository
from app.tasks.registry import TaskDefinitionRegistry
from app.tasks.repository import TaskRepository, TaskRunLogRepository, TaskRunRepository
from app.tasks.runner import TaskRunner
from app.tasks.runtime import TaskRuntimeRegistry
from app.tasks.service import TaskService


def get_task_runtime_registry(request: Request) -> TaskRuntimeRegistry:
    return cast(TaskRuntimeRegistry, request.app.state.task_runtime)


TaskRuntimeDep = Annotated[TaskRuntimeRegistry, Depends(get_task_runtime_registry)]


def get_task_registry(request: Request) -> TaskDefinitionRegistry:
    return cast(TaskDefinitionRegistry, request.app.state.task_registry)


TaskRegistryDep = Annotated[TaskDefinitionRegistry, Depends(get_task_registry)]


def get_task_service(
    pool: DbPool,
    request: Request,
    runtime_registry: TaskRuntimeDep,
    task_registry: TaskRegistryDep,
) -> TaskService:
    task_repo = TaskRepository(pool)
    run_repo = TaskRunRepository(pool)
    run_log_repo = TaskRunLogRepository(pool)
    log_repo = LogRepository(pool)
    runner = TaskRunner(
        pool=pool,
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        log_repo=log_repo,
        runtime_registry=runtime_registry,
        task_registry=task_registry,
        crawler_client=request.app.state.crawler_client,
        geo_client=request.app.state.geo_client,
    )
    return TaskService(
        task_repo=task_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
        runner=runner,
        task_registry=task_registry,
    )


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
