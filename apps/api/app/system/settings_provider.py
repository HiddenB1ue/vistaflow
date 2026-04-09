from __future__ import annotations

import asyncio
from time import monotonic

import asyncpg

from app.models import SystemSetting
from app.system.constants import OPTIONAL_STRING_SETTING_KEYS, SYSTEM_SETTING_KEYS
from app.system.setting_repository import SystemSettingRepository
from app.system.setting_values import parse_setting_value


class SystemSettingsDataError(RuntimeError):
    pass


class SystemSettingsProvider:
    def __init__(
        self,
        pool: asyncpg.Pool,
        *,
        ttl_seconds: float,
    ) -> None:
        self._repo = SystemSettingRepository(pool)
        self._ttl_seconds = ttl_seconds
        self._cached_settings: dict[str, SystemSetting] = {}
        self._loaded_at = 0.0
        self._lock = asyncio.Lock()

    async def invalidate(self) -> None:
        async with self._lock:
            self._cached_settings = {}
            self._loaded_at = 0.0

    async def list_settings(self) -> list[SystemSetting]:
        return list((await self._get_cached_settings()).values())

    async def get_optional_string(self, key: str) -> str:
        setting = await self._get_required_setting(key)
        if not setting.enabled:
            return ""
        if setting.value_type != "string":
            raise SystemSettingsDataError(f"配置 {key} 类型异常，预期 string")
        value = parse_setting_value(setting.value_type, setting.value)
        if not isinstance(value, str):
            raise SystemSettingsDataError(f"配置 {key} 解析结果不是字符串")
        return value

    async def get_int(self, key: str) -> int:
        value = await self._get_effective_value(key, expected_type="int")
        if not isinstance(value, int) or isinstance(value, bool):
            raise SystemSettingsDataError(f"配置 {key} 解析结果不是整数")
        return value

    async def get_float(self, key: str) -> float:
        value = await self._get_effective_value(key, expected_type="float")
        if not isinstance(value, float):
            raise SystemSettingsDataError(f"配置 {key} 解析结果不是浮点数")
        return value

    async def get_bool(self, key: str) -> bool:
        setting = await self._get_required_setting(key)
        if not setting.enabled:
            return False
        if setting.value_type != "bool":
            raise SystemSettingsDataError(f"配置 {key} 类型异常，预期 bool")
        value = parse_setting_value(setting.value_type, setting.value)
        if not isinstance(value, bool):
            raise SystemSettingsDataError(f"配置 {key} 解析结果不是布尔值")
        return value

    def get_cached_optional_string(self, key: str) -> str:
        setting = self._cached_settings.get(key)
        if setting is None or not setting.enabled:
            return ""
        if setting.value_type != "string":
            return ""
        try:
            value = parse_setting_value(setting.value_type, setting.value)
        except Exception:
            return ""
        return value if isinstance(value, str) else ""

    async def _get_effective_value(self, key: str, *, expected_type: str):
        setting = await self._get_required_setting(key)
        if not setting.enabled:
            if key in OPTIONAL_STRING_SETTING_KEYS:
                return ""
            raise SystemSettingsDataError(f"配置 {key} 已禁用，当前不可用")
        if setting.value_type != expected_type:
            raise SystemSettingsDataError(
                f"配置 {key} 类型异常，预期 {expected_type}，实际 {setting.value_type}"
            )
        try:
            return parse_setting_value(setting.value_type, setting.value)
        except Exception as exc:
            raise SystemSettingsDataError(f"配置 {key} 值非法：{exc}") from exc

    async def _get_required_setting(self, key: str) -> SystemSetting:
        settings = await self._get_cached_settings()
        setting = settings.get(key)
        if setting is None:
            raise SystemSettingsDataError(f"系统配置缺失：{key}")
        return setting

    async def _get_cached_settings(self) -> dict[str, SystemSetting]:
        if self._is_cache_fresh():
            return self._cached_settings

        async with self._lock:
            if self._is_cache_fresh():
                return self._cached_settings

            settings = {item.key: item for item in await self._repo.find_all()}
            missing = sorted(SYSTEM_SETTING_KEYS - settings.keys())
            if missing:
                raise SystemSettingsDataError(
                    f"系统配置初始化不完整，缺少：{', '.join(missing)}"
                )
            self._cached_settings = settings
            self._loaded_at = monotonic()
            return self._cached_settings

    def _is_cache_fresh(self) -> bool:
        if not self._cached_settings:
            return False
        return monotonic() - self._loaded_at < self._ttl_seconds
