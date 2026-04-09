from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.exceptions import BusinessError, NotFoundError
from app.system.constants import TOGGLE_SETTING_KEYS
from app.system.schemas import (
    SystemSettingBatchUpdateRequest,
    SystemSettingBatchUpdateResponse,
    SystemSettingResponse,
    ToggleResponse,
)
from app.system.setting_repository import SystemSettingRepository
from app.system.setting_values import parse_setting_value, serialize_setting_value
from app.system.settings_provider import SystemSettingsProvider


class SystemSettingService:
    def __init__(
        self,
        repo: SystemSettingRepository,
        provider: SystemSettingsProvider,
    ) -> None:
        self._repo = repo
        self._provider = provider

    async def list_settings(self) -> list[SystemSettingResponse]:
        settings = await self._repo.find_all()
        return [self._to_response(item) for item in settings]

    async def update_settings(
        self,
        payload: SystemSettingBatchUpdateRequest,
    ) -> SystemSettingBatchUpdateResponse:
        if not payload.items:
            raise BusinessError("系统配置更新列表不能为空", http_status=400)

        keys = [item.key for item in payload.items]
        duplicate_keys = sorted({key for key in keys if keys.count(key) > 1})
        if duplicate_keys:
            raise BusinessError(
                f"系统配置更新存在重复 key：{', '.join(duplicate_keys)}",
                http_status=400,
            )

        current_settings = {item.key: item for item in await self._repo.find_by_keys(keys)}
        missing_keys = [key for key in keys if key not in current_settings]
        if missing_keys:
            raise NotFoundError(f"系统配置不存在：{', '.join(missing_keys)}")

        normalized_items: list[tuple[str, str, bool]] = []
        for item in payload.items:
            current = current_settings[item.key]
            try:
                serialized_value = serialize_setting_value(current.value_type, item.value)
            except Exception as exc:
                raise BusinessError(
                    f"系统配置 {item.key} 的值无效：{exc}",
                    http_status=400,
                ) from exc
            normalized_items.append((item.key, serialized_value, item.enabled))

        updated = await self._repo.update_settings(normalized_items)
        await self._provider.invalidate()
        updated_at = max((item.updated_at for item in updated), default=datetime.now(UTC))
        return SystemSettingBatchUpdateResponse(
            updatedCount=len(updated),
            updatedKeys=[item.key for item in updated],
            updatedAt=updated_at,
        )

    async def list_toggles(self) -> list[ToggleResponse]:
        settings = await self._repo.find_all()
        toggles = [
            item
            for item in settings
            if item.key in TOGGLE_SETTING_KEYS and item.value_type == "bool"
        ]
        return [
            ToggleResponse(
                id=item.key,
                label=item.label,
                description=item.description or "",
                enabled=bool(parse_setting_value(item.value_type, item.value)) if item.enabled else False,
            )
            for item in toggles
        ]

    @staticmethod
    def _to_response(setting) -> SystemSettingResponse:
        value: Any
        try:
            value = parse_setting_value(setting.value_type, setting.value)
        except Exception as exc:
            raise BusinessError(
                f"系统配置 {setting.key} 的存储值非法：{exc}",
                http_status=500,
            ) from exc

        return SystemSettingResponse(
            key=setting.key,
            value=value,
            valueType=setting.value_type,
            category=setting.category,
            label=setting.label,
            description=setting.description,
            enabled=setting.enabled,
            updatedAt=setting.updated_at,
        )
