from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.models import SystemSetting
from app.system.settings_provider import SystemSettingsDataError, SystemSettingsProvider

NOW = datetime(2026, 4, 9, tzinfo=UTC)


def make_setting(
    *,
    key: str,
    value: str,
    value_type: str,
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
        description=None,
        enabled=enabled,
        created_at=NOW,
        updated_at=NOW,
    )


class FakeRepo:
    def __init__(self, settings: list[SystemSetting]) -> None:
        self.settings = settings
        self.calls = 0

    async def find_all(self) -> list[SystemSetting]:
        self.calls += 1
        return self.settings


def build_provider(settings: list[SystemSetting], ttl_seconds: float = 5.0) -> tuple[SystemSettingsProvider, FakeRepo]:
    provider = SystemSettingsProvider(MagicMock(), ttl_seconds=ttl_seconds)
    repo = FakeRepo(settings)
    provider._repo = repo  # type: ignore[attr-defined]
    return provider, repo


def test_provider_reads_typed_values_and_caches_results() -> None:
    provider, repo = build_provider(
        [
            make_setting(key="amap_api_key", value="demo-key", value_type="string"),
            make_setting(key="amap_max_retries", value="3", value_type="int"),
            make_setting(key="amap_retry_delay_seconds", value="1.5", value_type="float"),
            make_setting(key="amap_min_interval_seconds", value="0.8", value_type="float"),
            make_setting(key="amap_rate_limit_cooldown_seconds", value="5.0", value_type="float"),
            make_setting(key="ticket_12306_enabled", value="true", value_type="bool", category="ticket_12306"),
            make_setting(key="geo_enrich_enabled", value="true", value_type="bool", category="task"),
            make_setting(key="auto_crawl_enabled", value="false", value_type="bool", category="task"),
            make_setting(key="price_sync_enabled", value="false", value_type="bool", category="task"),
            make_setting(key="preview_write_enabled", value="false", value_type="bool", category="task"),
            make_setting(key="maintenance_mode", value="false", value_type="bool", category="system"),
        ]
    )

    assert asyncio.run(provider.get_optional_string("amap_api_key")) == "demo-key"
    assert asyncio.run(provider.get_int("amap_max_retries")) == 3
    assert asyncio.run(provider.get_float("amap_retry_delay_seconds")) == 1.5
    assert asyncio.run(provider.get_bool("geo_enrich_enabled")) is True
    assert repo.calls == 1


def test_provider_raises_when_seeded_settings_are_missing() -> None:
    provider, _repo = build_provider(
        [
            make_setting(key="amap_api_key", value="", value_type="string"),
        ]
    )

    with pytest.raises(SystemSettingsDataError, match="系统配置初始化不完整"):
        asyncio.run(provider.get_optional_string("amap_api_key"))


def test_provider_treats_disabled_bool_setting_as_false() -> None:
    provider, _repo = build_provider(
        [
            make_setting(key="amap_api_key", value="", value_type="string"),
            make_setting(key="amap_max_retries", value="3", value_type="int"),
            make_setting(key="amap_retry_delay_seconds", value="1.0", value_type="float"),
            make_setting(key="amap_min_interval_seconds", value="0.35", value_type="float"),
            make_setting(key="amap_rate_limit_cooldown_seconds", value="3.0", value_type="float"),
            make_setting(key="ticket_12306_enabled", value="false", value_type="bool", category="ticket_12306"),
            make_setting(key="geo_enrich_enabled", value="true", value_type="bool", category="task", enabled=False),
            make_setting(key="auto_crawl_enabled", value="false", value_type="bool", category="task"),
            make_setting(key="price_sync_enabled", value="false", value_type="bool", category="task"),
            make_setting(key="preview_write_enabled", value="false", value_type="bool", category="task"),
            make_setting(key="maintenance_mode", value="false", value_type="bool", category="system"),
        ]
    )

    assert asyncio.run(provider.get_bool("geo_enrich_enabled")) is False
