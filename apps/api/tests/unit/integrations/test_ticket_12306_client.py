from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from app.integrations.ticket_12306.client import (
    Live12306TicketClient,
    build_minimal_ticket_cookie,
    build_ticket_client,
)


def test_build_ticket_client_returns_none_when_setting_disabled() -> None:
    settings_provider = MagicMock()
    settings_provider.get_bool = AsyncMock(return_value=False)
    http_client = MagicMock()

    client = asyncio.run(build_ticket_client(settings_provider, http_client))

    assert client is None
    settings_provider.get_bool.assert_awaited_once_with("ticket_12306_enabled")


def test_build_ticket_client_returns_live_client_when_setting_enabled() -> None:
    settings_provider = MagicMock()
    settings_provider.get_bool = AsyncMock(return_value=True)
    http_client = MagicMock()

    client = asyncio.run(build_ticket_client(settings_provider, http_client))

    assert isinstance(client, Live12306TicketClient)
    settings_provider.get_bool.assert_awaited_once_with("ticket_12306_enabled")


def test_build_minimal_ticket_cookie_contains_constructed_query_fields() -> None:
    cookie = build_minimal_ticket_cookie(
        run_date="2026-05-01",
        from_station="北京",
        from_telecode="BJP",
        to_station="上海",
        to_telecode="SHH",
    )

    assert "_jc_save_fromStation=%u5317%u4EAC%2CBJP" in cookie
    assert "_jc_save_toStation=%u4E0A%u6D77%2CSHH" in cookie
    assert "_jc_save_wfdc_flag=dc" in cookie
    assert "_jc_save_fromDate=2026-05-01" in cookie
    assert f"_jc_save_toDate={date.today().isoformat()}" in cookie
    assert "guidesStatus=off" in cookie
    assert "highContrastMode=defaltMode" in cookie
    assert "cursorStatus=off" in cookie
