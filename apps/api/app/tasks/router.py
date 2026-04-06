from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.auth.dependencies import require_admin_auth
from app.schemas import APIResponse
from app.tasks.dependencies import TaskServiceDep
from app.tasks.schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskRunLogResponse,
    TaskRunResponse,
    TaskTypeResponse,
    TaskUpdateRequest,
)

router = APIRouter(tags=["tasks"], dependencies=[Depends(require_admin_auth)])


@router.get("/task-types", response_model=APIResponse[list[TaskTypeResponse]])
async def list_task_types(service: TaskServiceDep) -> APIResponse[list[TaskTypeResponse]]:
    return APIResponse.ok(await service.list_task_types())


@router.get("/tasks", response_model=APIResponse[list[TaskResponse]])
async def list_tasks(service: TaskServiceDep) -> APIResponse[list[TaskResponse]]:
    return APIResponse.ok(await service.list_tasks())


@router.post(
    "/tasks",
    response_model=APIResponse[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    payload: TaskCreateRequest,
    service: TaskServiceDep,
) -> APIResponse[TaskResponse]:
    return APIResponse.ok(await service.create_task(payload))


@router.get("/tasks/{task_id}", response_model=APIResponse[TaskResponse])
async def get_task(task_id: int, service: TaskServiceDep) -> APIResponse[TaskResponse]:
    return APIResponse.ok(await service.get_task(task_id))


@router.patch("/tasks/{task_id}", response_model=APIResponse[TaskResponse])
async def update_task(
    task_id: int,
    payload: TaskUpdateRequest,
    service: TaskServiceDep,
) -> APIResponse[TaskResponse]:
    return APIResponse.ok(await service.update_task(task_id, payload))


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, service: TaskServiceDep) -> Response:
    await service.delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/tasks/{task_id}/run",
    response_model=APIResponse[TaskRunResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_task(task_id: int, service: TaskServiceDep) -> APIResponse[TaskRunResponse]:
    return APIResponse.ok(await service.trigger_task(task_id))


@router.get(
    "/tasks/{task_id}/runs",
    response_model=APIResponse[list[TaskRunResponse]],
)
async def list_task_runs(
    task_id: int,
    service: TaskServiceDep,
) -> APIResponse[list[TaskRunResponse]]:
    return APIResponse.ok(await service.list_runs(task_id))


@router.get("/task-runs/{run_id}", response_model=APIResponse[TaskRunResponse])
async def get_task_run(
    run_id: int,
    service: TaskServiceDep,
) -> APIResponse[TaskRunResponse]:
    return APIResponse.ok(await service.get_run(run_id))


@router.get(
    "/task-runs/{run_id}/logs",
    response_model=APIResponse[list[TaskRunLogResponse]],
)
async def list_task_run_logs(
    run_id: int,
    service: TaskServiceDep,
) -> APIResponse[list[TaskRunLogResponse]]:
    return APIResponse.ok(await service.list_run_logs(run_id))


@router.post(
    "/task-runs/{run_id}/terminate",
    response_model=APIResponse[TaskRunResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def terminate_task_run(
    run_id: int,
    service: TaskServiceDep,
) -> APIResponse[TaskRunResponse]:
    return APIResponse.ok(await service.terminate_run(run_id))
