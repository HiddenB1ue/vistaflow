from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.railway.dependencies import DbPool
from app.system.log_repository import LogRepository
from app.tasks.repository import TaskRepository
from app.tasks.runner import TaskRunner
from app.tasks.service import TaskService


def get_task_service(pool: DbPool, request: Request) -> TaskService:
    task_repo = TaskRepository(pool)
    log_repo = LogRepository(pool)
    runner = TaskRunner(
        pool=pool,
        task_repo=task_repo,
        log_repo=log_repo,
        crawler_client=request.app.state.crawler_client,
        geo_client=request.app.state.geo_client,
    )
    return TaskService(repo=task_repo, runner=runner)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
