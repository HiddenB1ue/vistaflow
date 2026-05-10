from __future__ import annotations

import asyncio
from typing import Any

from app.integrations.ticket_12306.cookie_manager import (
    CookieBundle,
    Ticket12306CookieManager,
)


class InMemoryRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.locks: set[str] = set()

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        self.store[key] = value
        return True

    async def delete(self, key: str) -> int:
        existed = key in self.store
        self.store.pop(key, None)
        was_lock = key in self.locks
        self.locks.discard(key)
        return int(existed or was_lock)

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool | None:
        if nx and key in self.locks:
            return None
        self.locks.add(key)
        return True


class StubBrowserManager:
    """Returns deterministic cookies whenever ``run_with_browser`` is invoked."""

    def __init__(self, cookies: list[dict[str, Any]] | None = None) -> None:
        self.cookies = cookies if cookies is not None else [
            {"name": "JSESSIONID", "value": "abc123"},
            {"name": "BIGipServerotn", "value": "deadbeef"},
        ]
        self.calls = 0

    async def run_with_browser(self, callback: Any) -> Any:
        self.calls += 1
        browser = _FakeBrowser(self.cookies)
        return await callback(browser)


class _FakeBrowser:
    def __init__(self, cookies: list[dict[str, Any]]) -> None:
        self._cookies = cookies

    async def new_context(self, **_: Any) -> _FakeContext:
        return _FakeContext(self._cookies)


class _FakeContext:
    def __init__(self, cookies: list[dict[str, Any]]) -> None:
        self._cookies = cookies
        self.closed = False

    async def new_page(self) -> _FakePage:
        return _FakePage()

    async def cookies(self) -> list[dict[str, Any]]:
        return self._cookies

    async def close(self) -> None:
        self.closed = True


class _FakePage:
    def set_default_timeout(self, _: int) -> None:
        return None

    def set_default_navigation_timeout(self, _: int) -> None:
        return None

    async def goto(self, _url: str, *, wait_until: str, timeout: int) -> None:
        return None

    async def wait_for_load_state(self, _state: str, *, timeout: int) -> None:
        return None


def test_get_refreshes_when_cache_empty() -> None:
    redis_client = InMemoryRedis()
    browser_manager = StubBrowserManager()
    manager = Ticket12306CookieManager(
        redis_client=redis_client,  # type: ignore[arg-type]
        browser_manager=browser_manager,  # type: ignore[arg-type]
    )

    bundle = asyncio.run(manager.get())

    assert isinstance(bundle, CookieBundle)
    assert bundle.cookies == {"JSESSIONID": "abc123", "BIGipServerotn": "deadbeef"}
    assert browser_manager.calls == 1
    # Subsequent get() reads from cache without invoking browser again.
    bundle2 = asyncio.run(manager.get())
    assert bundle2.cookies == bundle.cookies
    assert browser_manager.calls == 1


def test_mark_invalid_forces_next_refresh() -> None:
    redis_client = InMemoryRedis()
    browser_manager = StubBrowserManager()
    manager = Ticket12306CookieManager(
        redis_client=redis_client,  # type: ignore[arg-type]
        browser_manager=browser_manager,  # type: ignore[arg-type]
    )

    asyncio.run(manager.get())
    assert browser_manager.calls == 1

    asyncio.run(manager.mark_invalid())
    asyncio.run(manager.get())
    assert browser_manager.calls == 2


def test_concurrent_refresh_reuses_single_browser_call() -> None:
    redis_client = InMemoryRedis()
    browser_manager = StubBrowserManager()
    manager = Ticket12306CookieManager(
        redis_client=redis_client,  # type: ignore[arg-type]
        browser_manager=browser_manager,  # type: ignore[arg-type]
    )

    async def race() -> tuple[CookieBundle, CookieBundle]:
        return await asyncio.gather(manager.get(), manager.get())

    a, b = asyncio.run(race())
    assert a.cookies == b.cookies
    # Local lock serialises the two callers in the same process so only the
    # first one drives Playwright; the second reuses the freshly-cached value.
    assert browser_manager.calls == 1


def test_refresh_now_skips_browser_when_peer_publishes_first() -> None:
    redis_client = InMemoryRedis()
    browser_manager = StubBrowserManager()
    manager = Ticket12306CookieManager(
        redis_client=redis_client,  # type: ignore[arg-type]
        browser_manager=browser_manager,  # type: ignore[arg-type]
    )

    # Simulate another worker holding the lock and publishing cookies before
    # we exhaust the wait window.
    async def scenario() -> CookieBundle:
        # Pre-occupy the lock so our refresh_now waits.
        await redis_client.set(
            "ticket_12306:cookies:refresh_lock", "1", ex=30, nx=True
        )

        async def publish_after_delay() -> None:
            await asyncio.sleep(0.4)
            await redis_client.setex(
                "ticket_12306:cookies:v1",
                1500,
                '{"cookies": {"x": "y"}, "user_agent": "ua", "refreshed_at": 1.0}',
            )

        publisher = asyncio.create_task(publish_after_delay())
        try:
            return await manager.refresh_now()
        finally:
            await publisher

    bundle = asyncio.run(scenario())
    assert bundle.cookies == {"x": "y"}
    assert browser_manager.calls == 0


def test_get_handles_corrupted_cache_payload() -> None:
    redis_client = InMemoryRedis()
    redis_client.store["ticket_12306:cookies:v1"] = "not-json"
    browser_manager = StubBrowserManager()
    manager = Ticket12306CookieManager(
        redis_client=redis_client,  # type: ignore[arg-type]
        browser_manager=browser_manager,  # type: ignore[arg-type]
    )

    bundle = asyncio.run(manager.get())
    assert bundle.cookies == {"JSESSIONID": "abc123", "BIGipServerotn": "deadbeef"}
    assert browser_manager.calls == 1


def test_browser_navigation_failure_is_swallowed_and_cookies_returned(
    monkeypatch: Any,
) -> None:
    redis_client = InMemoryRedis()
    browser_manager = StubBrowserManager()
    manager = Ticket12306CookieManager(
        redis_client=redis_client,  # type: ignore[arg-type]
        browser_manager=browser_manager,  # type: ignore[arg-type]
    )

    # Force the page navigation to raise; cookies should still be collected
    # from whatever the context already has.
    original_new_page = _FakeContext.new_page

    async def failing_page(self: _FakeContext) -> Any:
        page = await original_new_page(self)

        async def raising_goto(
            _url: str, *, wait_until: str, timeout: int
        ) -> None:
            raise RuntimeError("navigation failed")

        page.goto = raising_goto  # type: ignore[method-assign]
        return page

    monkeypatch.setattr(_FakeContext, "new_page", failing_page)

    bundle = asyncio.run(manager.get())
    assert bundle.cookies  # cookies still extracted from the context
