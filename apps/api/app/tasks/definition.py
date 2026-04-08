from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.tasks.execution import TaskExecutionContext, TaskExecutionResult

TaskType = Literal[
    "fetch-station",
    "fetch-trains",
    "fetch-train-stops",
    "fetch-train-runs",
    "price",
]
TaskStatus = Literal["idle", "pending", "running", "completed", "error", "terminated"]
TaskRunStatus = Literal["pending", "running", "completed", "error", "terminated"]
TaskTriggerMode = Literal["manual"]
TaskValueType = Literal["date", "text"]
TaskExecutor = Callable[["TaskExecutionContext"], Awaitable["TaskExecutionResult"]]


@dataclass(frozen=True)
class TaskParamDefinition:
    key: str
    label: str
    value_type: TaskValueType
    required: bool
    placeholder: str
    description: str


@dataclass(frozen=True)
class TaskCapabilityContract:
    can_run: bool = True
    can_terminate: bool = True
    supports_progress_snapshot: bool = True
    supports_cron: bool = True


@dataclass(frozen=True)
class TaskTypeDefinition:
    type: str
    label: str
    description: str
    implemented: bool
    capability: TaskCapabilityContract = field(default_factory=TaskCapabilityContract)
    param_schema: tuple[TaskParamDefinition, ...] = field(default_factory=tuple)
    payload_model: type[BaseModel] | None = None
    executor: TaskExecutor | None = None

    @property
    def supports_cron(self) -> bool:
        return self.capability.supports_cron
