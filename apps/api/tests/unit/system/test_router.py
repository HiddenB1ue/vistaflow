from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from app.system.router import list_settings, list_toggles, update_settings
from app.system.schemas import (
    SystemSettingBatchUpdateRequest,
    SystemSettingBatchUpdateItemRequest,
    SystemSettingBatchUpdateResponse,
    SystemSettingResponse,
    ToggleResponse,
)

NOW = datetime(2026, 4, 9, tzinfo=UTC)


def make_service() -> MagicMock:
    service = MagicMock()
    service.list_settings = AsyncMock(
        return_value=[
            SystemSettingResponse(
                key="amap_api_key",
                value="demo-key",
                valueType="string",
                category="amap",
                label="高德 API Key",
                description="desc",
                enabled=True,
                updatedAt=NOW,
            )
        ]
    )
    service.update_settings = AsyncMock(
        return_value=SystemSettingBatchUpdateResponse(
            updatedCount=1,
            updatedKeys=["amap_api_key"],
            updatedAt=NOW,
        )
    )
    service.list_toggles = AsyncMock(
        return_value=[
            ToggleResponse(
                id="maintenance_mode",
                label="维护模式",
                description="desc",
                enabled=False,
            )
        ]
    )
    return service


def test_list_system_settings() -> None:
    service = make_service()

    response = asyncio.run(list_settings(service))

    assert response.data is not None
    assert response.data[0].key == "amap_api_key"
    assert response.data[0].value == "demo-key"


def test_update_system_settings() -> None:
    service = make_service()

    response = asyncio.run(
        update_settings(
            SystemSettingBatchUpdateRequest(
                items=[
                    SystemSettingBatchUpdateItemRequest(
                        key="amap_api_key",
                        value="new-key",
                        enabled=True,
                    )
                ]
            ),
            service,
        )
    )

    assert response.data is not None
    assert response.data.updatedKeys == ["amap_api_key"]
    service.update_settings.assert_awaited_once()


def test_list_toggles_uses_setting_service() -> None:
    service = make_service()

    response = asyncio.run(list_toggles(service))

    assert response.data is not None
    assert response.data[0].id == "maintenance_mode"
