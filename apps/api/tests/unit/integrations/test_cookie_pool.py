from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock

from app.integrations.ticket_12306.cookie_manager import CookieBundle
from app.integrations.ticket_12306.cookie_pool import CookiePool


class FakeRedis:
    """Minimal fake Redis for cookie pool tests."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self.store[key] = value

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)


class FakeBrowserManager:
    """Returns a browser whose contexts yield preset cookies."""

    def __init__(self, cookies: dict[str, str] | None = None) -> None:
        self.cookies = cookies or {"RAIL_EXPIRATION": "abc", "RAIL_DEVICEID": "xyz"}
        self.calls = 0

    async def run_with_browser(self, callback: Any) -> Any:
        self.calls += 1
        browser = _FakeBrowser(self.cookies)
        return await callback(browser)


class _FakeBrowser:
    def __init__(self, cookies: dict[str, str]) -> None:
        self._cookies = cookies

    async def new_context(self, **kwargs: Any) -> _FakeContext:
        return _FakeContext(self._cookies)


class _FakeContext:
    def __init__(self, cookies: dict[str, str]) -> None:
        self._cookies = cookies
        self.closed = False

    async def new_page(self) -> _FakePage:
        return _FakePage()

    async def cookies(self) -> list[dict[str, str]]:
        return [{"name": k, "value": v} for k, v in self._cookies.items()]

    async def close(self) -> None:
        self.closed = True


class _FakePage:
    def set_default_timeout(self, ms: int) -> None:
        pass

    def set_default_navigation_timeout(self, ms: int) -> None:
        pass

    async def goto(self, url: str, **kwargs: Any) -> None:
        pass

    async def wait_for_load_state(self, state: str, **kwargs: Any) -> None:
        pass


def _seed_slot(redis: FakeRedis, slot_id: int, cookies: dict[str, str] | None = None) -> None:
    """Write a CookieBundle JSON into a slot key."""
    payload = {
        "cookies": cookies or {"RAIL_EXPIRATION": f"val{slot_id}"},
        "user_agent": "ua",
        "refreshed_at": 1000.0 + slot_id,
    }
    key = f"ticket_12306:cookie_pool:slot:{slot_id}"
    redis.store[key] = json.dumps(payload)


def test_get_returns_seeded_bundle() -> None:
    redis = FakeRedis()
    bm = FakeBrowserManager()
    pool = CookiePool(redis, bm, pool_size=3)  # type: ignore[arg-type]
    _seed_slot(redis, 0)

    bundle = asyncio.run(pool.get())

    assert bundle.slot_id == 0
    assert "RAIL_EXPIRATION" in bundle.cookies
    assert bm.calls == 0  # no Playwright needed


def test_get_round_robins_across_slots() -> None:
    redis = FakeRedis()
    bm = FakeBrowserManager()
    pool = CookiePool(redis, bm, pool_size=3)  # type: ignore[arg-type]
    _seed_slot(redis, 0)
    _seed_slot(redis, 1)
    _seed_slot(redis, 2)

    async def get_three() -> list[int]:
        return [
            (await pool.get()).slot_id,
            (await pool.get()).slot_id,
            (await pool.get()).slot_id,
        ]

    slot_ids = asyncio.run(get_three())
    assert slot_ids == [0, 1, 2]


def test_get_skips_empty_slots() -> None:
    redis = FakeRedis()
    bm = FakeBrowserManager()
    pool = CookiePool(redis, bm, pool_size=3)  # type: ignore[arg-type]
    # Only slot 2 is seeded
    _seed_slot(redis, 2)

    bundle = asyncio.run(pool.get())
    assert bundle.slot_id == 2


def test_get_refreshes_when_all_empty() -> None:
    redis = FakeRedis()
    bm = FakeBrowserManager()
    pool = CookiePool(redis, bm, pool_size=2)  # type: ignore[arg-type]
    # No slots seeded

    bundle = asyncio.run(pool.get())

    assert bundle.slot_id == 0  # refreshed slot 0
    assert bm.calls == 1
    assert "RAIL_EXPIRATION" in bundle.cookies


def test_mark_invalid_removes_slot() -> None:
    redis = FakeRedis()
    bm = FakeBrowserManager()
    pool = CookiePool(redis, bm, pool_size=2)  # type: ignore[arg-type]
    _seed_slot(redis, 0)
    _seed_slot(redis, 1)

    bundle = asyncio.run(pool.get())
    assert bundle.slot_id == 0

    asyncio.run(pool.mark_invalid(bundle))
    # Slot 0 should be gone
    assert "ticket_12306:cookie_pool:slot:0" not in redis.store
    assert "ticket_12306:cookie_pool:slot:1" in redis.store


def test_mark_invalid_noop_without_bundle() -> None:
    redis = FakeRedis()
    bm = FakeBrowserManager()
    pool = CookiePool(redis, bm, pool_size=1)  # type: ignore[arg-type]
    _seed_slot(redis, 0)

    # Should not raise
    asyncio.run(pool.mark_invalid(None))
    assert "ticket_12306:cookie_pool:slot:0" in redis.store


def test_refresh_pool_fills_empty_slots() -> None:
    redis = FakeRedis()
    bm = FakeBrowserManager()
    pool = CookiePool(redis, bm, pool_size=3)  # type: ignore[arg-type]
    _seed_slot(redis, 1)  # only slot 1 exists

    refreshed = asyncio.run(pool.refresh_pool())

    assert refreshed == 2  # slots 0 and 2
    assert bm.calls == 2
    assert "ticket_12306:cookie_pool:slot:0" in redis.store
    assert "ticket_12306:cookie_pool:slot:2" in redis.store


def test_refresh_pool_noop_when_full() -> None:
    redis = FakeRedis()
    bm = FakeBrowserManager()
    pool = CookiePool(redis, bm, pool_size=2)  # type: ignore[arg-type]
    _seed_slot(redis, 0)
    _seed_slot(redis, 1)

    refreshed = asyncio.run(pool.refresh_pool())

    assert refreshed == 0
    assert bm.calls == 0


def test_status_returns_slot_info() -> None:
    redis = FakeRedis()
    bm = FakeBrowserManager()
    pool = CookiePool(redis, bm, pool_size=2)  # type: ignore[arg-type]
    _seed_slot(redis, 0)

    slots = asyncio.run(pool.status())

    assert len(slots) == 2
    assert slots[0]["slot_id"] == 0
    assert slots[0]["valid"] is True
    assert slots[1]["slot_id"] == 1
    assert slots[1]["valid"] is False
