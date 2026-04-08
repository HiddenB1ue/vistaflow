from __future__ import annotations

from typing import Any

from app.tasks.definition import TaskTypeDefinition
from app.tasks.payloads import normalize_task_payload_with_model
from app.tasks.types import get_builtin_task_definitions


class TaskDefinitionRegistrationError(RuntimeError):
    pass


class TaskDefinitionRegistry:
    def __init__(self, definitions: tuple[TaskTypeDefinition, ...]) -> None:
        self._definitions: dict[str, TaskTypeDefinition] = {}
        for definition in definitions:
            self._register(definition)

    def _register(self, definition: TaskTypeDefinition) -> None:
        if definition.type in self._definitions:
            raise TaskDefinitionRegistrationError(f"任务类型 {definition.type} 重复注册")
        if definition.implemented and definition.executor is None:
            raise TaskDefinitionRegistrationError(
                f"任务类型 {definition.type} 已标记为可实现，但缺少执行入口"
            )
        if definition.capability.can_run and definition.executor is None and definition.implemented:
            raise TaskDefinitionRegistrationError(
                f"任务类型 {definition.type} 声明可执行，但缺少执行入口"
            )
        self._definitions[definition.type] = definition

    def all(self) -> list[TaskTypeDefinition]:
        return list(self._definitions.values())

    def keys(self) -> set[str]:
        return set(self._definitions.keys())

    def get_optional(self, task_type: str) -> TaskTypeDefinition | None:
        return self._definitions.get(task_type)

    def get_required(self, task_type: str) -> TaskTypeDefinition:
        definition = self.get_optional(task_type)
        if definition is None:
            raise TaskDefinitionRegistrationError(f"未注册的任务类型：{task_type}")
        return definition

    def normalize_payload(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        definition = self.get_required(task_type)
        return normalize_task_payload_with_model(task_type, payload, definition.payload_model)


_BUILTIN_REGISTRY: TaskDefinitionRegistry | None = None


def get_builtin_task_registry() -> TaskDefinitionRegistry:
    global _BUILTIN_REGISTRY
    if _BUILTIN_REGISTRY is None:
        _BUILTIN_REGISTRY = TaskDefinitionRegistry(get_builtin_task_definitions())
    return _BUILTIN_REGISTRY


def create_task_registry() -> TaskDefinitionRegistry:
    return TaskDefinitionRegistry(get_builtin_task_definitions())
