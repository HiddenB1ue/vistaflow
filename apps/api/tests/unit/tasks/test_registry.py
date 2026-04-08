from __future__ import annotations

import pytest
from pydantic import BaseModel, field_validator

from app.tasks.definition import TaskCapabilityContract, TaskTypeDefinition
from app.tasks.registry import TaskDefinitionRegistrationError, TaskDefinitionRegistry


async def fake_executor(_: object) -> object:
    return object()


class DemoPayload(BaseModel):
    keyword: str

    @field_validator("keyword")
    @classmethod
    def normalize_keyword(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("keyword 不能为空")
        return cleaned.upper()


def test_registry_rejects_duplicate_task_types() -> None:
    definition = TaskTypeDefinition(
        type="demo-task",
        label="Demo",
        description="demo",
        implemented=True,
        capability=TaskCapabilityContract(),
        executor=fake_executor,
    )

    with pytest.raises(TaskDefinitionRegistrationError):
        TaskDefinitionRegistry((definition, definition))


def test_registry_rejects_implemented_task_without_executor() -> None:
    definition = TaskTypeDefinition(
        type="broken-task",
        label="Broken",
        description="broken",
        implemented=True,
        capability=TaskCapabilityContract(),
    )

    with pytest.raises(TaskDefinitionRegistrationError):
        TaskDefinitionRegistry((definition,))


def test_registry_normalize_payload_uses_task_owned_model() -> None:
    registry = TaskDefinitionRegistry(
        (
            TaskTypeDefinition(
                type="demo-task",
                label="Demo",
                description="demo",
                implemented=True,
                capability=TaskCapabilityContract(),
                payload_model=DemoPayload,
                executor=fake_executor,
            ),
        )
    )

    assert registry.normalize_payload("demo-task", {"keyword": " g123 "}) == {
        "keyword": "G123",
    }
