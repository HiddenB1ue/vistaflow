from __future__ import annotations

from app.exceptions import BusinessError, NotFoundError


class TaskNotFound(NotFoundError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"任务 {task_id} 不存在")


class TaskAlreadyRunning(BusinessError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"任务 {task_id} 正在运行中", http_status=409)
