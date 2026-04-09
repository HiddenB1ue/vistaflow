from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.exceptions import BusinessError
from app.models import SystemSetting
from app.system.schemas import SystemSettingBatchUpdateRequest, SystemSettingBatchUpdateItemRequest
from app.system.settings_service import SystemSettingService

NOW = datetime(2026, 4, 9, tzinfo=UTC)


def make_setting(
    *,
    key: str = "amap_min_interval_seconds",
    value: str = "0.35",
    value_type: str = "float",
    category: str = "amap",
    enabled: bool = True,
) -> SystemSetting:
    return SystemSetting(
        id=1,
        key=key,
        value=value,
        value_type=value_type,
        category=category,
        label=key,
        description="desc",
        enabled=enabled,
        created_at=NOW,
        updated_at=NOW,
    )


def test_update_settings_normalizes_values_and_invalidates_provider() -> None:
    repo = AsyncMock()
    provider = AsyncMock()
    repo.find_by_keys.return_value = [make_setting()]
    repo.update_settings.return_value = [make_setting(value="1.0")]
    service = SystemSettingService(repo=repo, provider=provider)

    result = asyncio.run(
        service.update_settings(
            SystemSettingBatchUpdateRequest(
                items=[
                    SystemSettingBatchUpdateItemRequest(
                        key="amap_min_interval_seconds",
                        value="1.0",
                        enabled=True,
                    )
                ]
            ),
        )
    )

    assert result.updatedCount == 1
    assert result.updatedKeys == ["amap_min_interval_seconds"]
    assert repo.update_settings.await_args.args[0] == [("amap_min_interval_seconds", "1.0", True)]
    provider.invalidate.assert_awaited_once()


def test_update_settings_rejects_invalid_value() -> None:
    repo = AsyncMock()
    provider = AsyncMock()
    repo.find_by_keys.return_value = [make_setting(value_type="int", value="3", key="amap_max_retries")]
    service = SystemSettingService(repo=repo, provider=provider)

    with pytest.raises(BusinessError, match="值无效"):
        asyncio.run(
            service.update_settings(
                SystemSettingBatchUpdateRequest(
                    items=[
                        SystemSettingBatchUpdateItemRequest(
                            key="amap_max_retries",
                            value="bad-int",
                            enabled=True,
                        )
                    ]
                ),
            )
        )


def test_update_settings_rejects_duplicate_keys() -> None:
    repo = AsyncMock()
    provider = AsyncMock()
    service = SystemSettingService(repo=repo, provider=provider)

    with pytest.raises(BusinessError, match="重复 key"):
        asyncio.run(
            service.update_settings(
                SystemSettingBatchUpdateRequest(
                    items=[
                        SystemSettingBatchUpdateItemRequest(key="maintenance_mode", value=True, enabled=True),
                        SystemSettingBatchUpdateItemRequest(key="maintenance_mode", value=False, enabled=True),
                    ]
                )
            )
        )
