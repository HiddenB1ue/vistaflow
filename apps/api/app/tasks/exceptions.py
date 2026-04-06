from __future__ import annotations

from app.exceptions import BusinessError, NotFoundError


class TaskNotFound(NotFoundError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"任务 {task_id} 不存在")


class TaskRunNotFound(NotFoundError):
    def __init__(self, run_id: int) -> None:
        super().__init__(f"任务执行 {run_id} 不存在")


class TaskNameConflict(BusinessError):
    def __init__(self, name: str) -> None:
        super().__init__(f"任务名称“{name}”已存在", http_status=409)


class TaskTypeUnsupported(BusinessError):
    def __init__(self, task_type: str) -> None:
        super().__init__(f"任务类型“{task_type}”不受支持", http_status=400)


class TaskTypeNotImplemented(BusinessError):
    def __init__(self, task_type: str) -> None:
        super().__init__(
            f"任务类型“{task_type}”当前尚未提供可执行实现",
            http_status=409,
        )


class TaskPayloadValidationError(BusinessError):
    def __init__(self, task_type: str, detail: str) -> None:
        super().__init__(f"任务类型“{task_type}”的参数无效：{detail}", http_status=400)


class TaskDisabled(BusinessError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"任务 {task_id} 已停用，不能执行", http_status=409)


class TaskAlreadyRunning(BusinessError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"任务 {task_id} 正在运行中", http_status=409)


class TaskUpdateConflict(BusinessError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"任务 {task_id} 正在运行中，暂不允许修改", http_status=409)


class TaskDeleteConflict(BusinessError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"任务 {task_id} 正在运行中，不能删除", http_status=409)


class TaskRunNotTerminable(BusinessError):
    def __init__(self, run_id: int) -> None:
        super().__init__(f"任务执行 {run_id} 当前不可终止", http_status=409)


class TaskExecutionError(RuntimeError):
    pass
