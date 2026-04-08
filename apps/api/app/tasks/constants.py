from __future__ import annotations

from app.tasks.definition import (
    TaskParamDefinition,
    TaskTypeDefinition,
)
from app.tasks.registry import get_builtin_task_registry

TASK_TYPES: dict[str, TaskTypeDefinition] = {
    definition.type: definition for definition in get_builtin_task_registry().all()
}

RUNNABLE_TASK_TYPES: frozenset[str] = frozenset(
    task_type
    for task_type, definition in TASK_TYPES.items()
    if definition.implemented and definition.capability.can_run
)


def get_task_type_definition(task_type: str) -> TaskTypeDefinition | None:
    return TASK_TYPES.get(task_type)


def get_task_type_label(task_type: str) -> str:
    definition = get_task_type_definition(task_type)
    return definition.label if definition is not None else task_type


def get_task_type_param_schema(task_type: str) -> tuple[TaskParamDefinition, ...]:
    definition = get_task_type_definition(task_type)
    return definition.param_schema if definition is not None else ()


def is_supported_task_type(task_type: str) -> bool:
    return task_type in TASK_TYPES


def is_implemented_task_type(task_type: str) -> bool:
    definition = get_task_type_definition(task_type)
    return definition.implemented if definition is not None else False
