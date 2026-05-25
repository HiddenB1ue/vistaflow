from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from app.journey_search_sessions.dependencies import get_ticket_service
from app.system.settings_provider import SystemSettingsDataError


@pytest.mark.asyncio
async def test_get_ticket_service_uses_configured_cache_ttl() -> None:
    settings_provider = MagicMock()
    settings_provider.get_int = AsyncMock(return_value=1800)
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                system_settings_provider=settings_provider,
            )
        )
    )

    with patch(
        "app.journey_search_sessions.dependencies.build_ticket_client",
        new=AsyncMock(return_value=MagicMock()),
    ):
        service = await get_ticket_service(
            cast(Request, request),
            redis_client=MagicMock(),
            pool=MagicMock(),
        )

    settings_provider.get_int.assert_awaited_once_with("ticket_12306_cache_ttl_seconds")
    assert service._cache_ttl_seconds == 1800


@pytest.mark.asyncio
async def test_get_ticket_service_falls_back_when_cache_ttl_setting_is_invalid() -> None:
    settings_provider = MagicMock()
    settings_provider.get_int = AsyncMock(side_effect=SystemSettingsDataError("invalid"))
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                system_settings_provider=settings_provider,
            )
        )
    )

    with patch(
        "app.journey_search_sessions.dependencies.build_ticket_client",
        new=AsyncMock(return_value=MagicMock()),
    ):
        service = await get_ticket_service(
            cast(Request, request),
            redis_client=MagicMock(),
            pool=MagicMock(),
        )

    assert service._cache_ttl_seconds == 600
