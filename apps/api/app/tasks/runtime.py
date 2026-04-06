from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class ActiveTaskRun:
    run_id: int
    task_id: int
    task: asyncio.Task[None]


class TaskRuntimeRegistry:
    def __init__(self) -> None:
        self._by_run_id: dict[int, ActiveTaskRun] = {}
        self._run_id_by_task_id: dict[int, int] = {}

    def register(self, run_id: int, task_id: int, task: asyncio.Task[None]) -> None:
        self._by_run_id[run_id] = ActiveTaskRun(run_id=run_id, task_id=task_id, task=task)
        self._run_id_by_task_id[task_id] = run_id

    def unregister(self, run_id: int) -> None:
        active = self._by_run_id.pop(run_id, None)
        if active is not None:
            self._run_id_by_task_id.pop(active.task_id, None)

    def get_run(self, run_id: int) -> ActiveTaskRun | None:
        return self._by_run_id.get(run_id)

    def get_task_run(self, task_id: int) -> ActiveTaskRun | None:
        run_id = self._run_id_by_task_id.get(task_id)
        if run_id is None:
            return None
        return self._by_run_id.get(run_id)
