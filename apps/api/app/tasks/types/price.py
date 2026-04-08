from __future__ import annotations

from app.tasks.definition import TaskCapabilityContract, TaskTypeDefinition

TASK_TYPE_DEFINITION = TaskTypeDefinition(
    type="price",
    label="获取某个车次行程的余票信息",
    description="预留的余票查询任务类型，后续将接入 Redis 做实时缓存，当前暂未实现。",
    implemented=False,
    capability=TaskCapabilityContract(
        can_run=False,
        can_terminate=False,
        supports_progress_snapshot=False,
        supports_cron=True,
    ),
)
