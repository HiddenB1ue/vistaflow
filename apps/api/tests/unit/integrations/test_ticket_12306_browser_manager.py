from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.integrations.ticket_12306.browser_manager import (
    PlaywrightBrowserManager,
    PlaywrightUnavailableError,
)


def test_get_browser_raises_clear_error_when_playwright_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = PlaywrightBrowserManager()

    def _raise_missing(_: str) -> None:
        raise ModuleNotFoundError("playwright.async_api")

    monkeypatch.setattr(
        "app.integrations.ticket_12306.browser_manager.importlib.import_module",
        _raise_missing,
    )

    with pytest.raises(PlaywrightUnavailableError, match="uv sync"):
        asyncio.run(manager.get_browser())


def test_get_browser_raises_clear_error_when_chromium_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = PlaywrightBrowserManager()
    playwright = MagicMock()
    playwright.stop = AsyncMock()
    chromium = MagicMock()
    chromium.launch = AsyncMock(
        side_effect=RuntimeError(
            "Executable doesn't exist at /tmp/chromium. Please run the following command"
        )
    )
    playwright.chromium = chromium
    starter = MagicMock()
    starter.start = AsyncMock(return_value=playwright)
    async_api = MagicMock(async_playwright=MagicMock(return_value=starter))

    monkeypatch.setattr(
        "app.integrations.ticket_12306.browser_manager.importlib.import_module",
        lambda _: async_api,
    )

    with pytest.raises(PlaywrightUnavailableError, match="playwright install chromium"):
        asyncio.run(manager.get_browser())
