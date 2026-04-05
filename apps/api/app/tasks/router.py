from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_admin_auth
from app.schemas import APIResponse
from app.tasks.dependencies import TaskServiceDep
from app.tasks.schemas import TaskResponse

router = APIRouter(tags=["tasks"], dependencies=[Depends(require_admin_auth)])


@router.get("/tasks", response_model=APIResponse[list[TaskResponse]])
async def list_tasks(service: TaskServiceDep) -> APIResponse[list[TaskResponse]]:
    tasks = await service.list_tasks()
    return APIResponse.ok(tasks)


@router.post("/tasks/{task_id}/run", response_model=APIResponse[TaskResponse], status_code=202)
async def run_task(task_id: int, service: TaskServiceDep) -> APIResponse[TaskResponse]:
    task = await service.trigger_task(task_id)
    return APIResponse.ok(task)
