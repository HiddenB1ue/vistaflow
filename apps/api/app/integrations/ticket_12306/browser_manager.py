from __future__ import annotations

import asyncio
import importlib
import sys
import threading
from collections.abc import Awaitable, Callable
from concurrent.futures import Future
from contextlib import suppress
from typing import Any, TypeVar

from app.exceptions import ExternalServiceError

T = TypeVar("T")


class PlaywrightUnavailableError(ExternalServiceError):
    """Raised when Playwright or Chromium is unavailable locally."""


class PlaywrightBrowserManager:
    def __init__(
        self,
        *,
        headless: bool = True,
        launch_timeout_ms: int = 15_000,
    ) -> None:
        self._headless = headless
        self._launch_timeout_ms = launch_timeout_ms
        self._playwright: Any | None = None
        self._browser: Any | None = None
        self._async_lock: asyncio.Lock | None = None
        self._thread_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._thread_loop: asyncio.AbstractEventLoop | None = None

    async def get_browser(self) -> Any:
        if self._uses_thread_loop:
            loop = self._ensure_thread_loop()
            future = asyncio.run_coroutine_threadsafe(
                self._get_browser_in_current_loop(),
                loop,
            )
            return await asyncio.wrap_future(future)
        return await self._get_browser_in_current_loop()

    async def run_with_browser(
        self,
        callback: Callable[[Any], Awaitable[T]],
    ) -> T:
        if not self._uses_thread_loop:
            browser = await self._get_browser_in_current_loop()
            return await callback(browser)

        loop = self._ensure_thread_loop()
        future = asyncio.run_coroutine_threadsafe(
            self._run_with_browser_in_thread_loop(callback),
            loop,
        )
        return await asyncio.wrap_future(future)

    async def _run_with_browser_in_thread_loop(
        self,
        callback: Callable[[Any], Awaitable[T]],
    ) -> T:
        browser = await self._get_browser_in_current_loop()
        return await callback(browser)

    async def _get_browser_in_current_loop(self) -> Any:
        browser = self._browser
        if browser is not None and self._is_browser_connected(browser):
            return browser

        if self._async_lock is None:
            self._async_lock = asyncio.Lock()

        async with self._async_lock:
            browser = self._browser
            if browser is not None and self._is_browser_connected(browser):
                return browser

            await self._close_unlocked()

            try:
                async_api = importlib.import_module("playwright.async_api")
            except ModuleNotFoundError as exc:
                raise PlaywrightUnavailableError(
                    "Playwright Python package is not installed. Run `uv sync` in `apps/api`."
                ) from exc

            try:
                self._playwright = await async_api.async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self._headless,
                    timeout=self._launch_timeout_ms,
                )
            except Exception as exc:
                await self._close_unlocked()
                raise self._map_launch_error(exc) from exc

            return self._browser

    async def close(self) -> None:
        if self._uses_thread_loop and self._thread_loop is not None:
            loop = self._thread_loop
            close_future = asyncio.run_coroutine_threadsafe(
                self._close_in_current_loop(),
                loop,
            )
            await asyncio.wrap_future(close_future)
            stop_future: Future[None] = Future()

            def _stop_loop() -> None:
                loop.stop()
                stop_future.set_result(None)

            loop.call_soon_threadsafe(_stop_loop)
            await asyncio.wrap_future(stop_future)
            thread = self._thread
            if thread is not None:
                await asyncio.to_thread(thread.join, 5)
            self._thread = None
            self._thread_loop = None
            return

        await self._close_in_current_loop()

    async def _close_in_current_loop(self) -> None:
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        async with self._async_lock:
            await self._close_unlocked()

    async def _close_unlocked(self) -> None:
        browser = self._browser
        playwright = self._playwright
        self._browser = None
        self._playwright = None

        if browser is not None:
            with suppress(Exception):
                await browser.close()

        if playwright is not None:
            with suppress(Exception):
                await playwright.stop()

    def _is_browser_connected(self, browser: Any) -> bool:
        is_connected = getattr(browser, "is_connected", None)
        if callable(is_connected):
            try:
                return bool(is_connected())
            except Exception:
                return False
        return True

    def _map_launch_error(self, exc: Exception) -> PlaywrightUnavailableError:
        normalized = str(exc).lower()
        if (
            "executable doesn't exist" in normalized
            or "please run the following command" in normalized
        ):
            return PlaywrightUnavailableError(
                "Chromium browser binary is not installed. "
                "Run `python -m playwright install chromium`."
            )
        return PlaywrightUnavailableError(
            "Unable to start Playwright Chromium. "
            "Run `python -m playwright install chromium` and retry."
        )

    @property
    def _uses_thread_loop(self) -> bool:
        return sys.platform == "win32"

    def _ensure_thread_loop(self) -> asyncio.AbstractEventLoop:
        with self._thread_lock:
            loop = self._thread_loop
            if loop is not None and loop.is_running():
                return loop

            ready = threading.Event()
            errors: list[BaseException] = []

            def _run_loop() -> None:
                try:
                    if sys.platform == "win32":
                        loop = asyncio.ProactorEventLoop()  # type: ignore[attr-defined]
                    else:
                        loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    self._thread_loop = loop
                    ready.set()
                    loop.run_forever()
                    loop.close()
                except BaseException as exc:
                    errors.append(exc)
                    ready.set()

            self._thread = threading.Thread(
                target=_run_loop,
                name="ticket-12306-playwright",
                daemon=True,
            )
            self._thread.start()
            ready.wait(timeout=5)

            if errors:
                raise PlaywrightUnavailableError(
                    "Unable to start Playwright background event loop."
                ) from errors[0]

            if self._thread_loop is None:
                raise PlaywrightUnavailableError(
                    "Timed out while starting Playwright background event loop."
                )
            return self._thread_loop
