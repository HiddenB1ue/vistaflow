from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from time import time
from typing import Any

from redis.asyncio import Redis

from app.integrations.ticket_12306.browser_manager import (
    PlaywrightBrowserManager,
    PlaywrightUnavailableError,
)
from app.integrations.ticket_12306.parser import BASE_HEADERS

logger = logging.getLogger(__name__)

_COOKIE_REDIS_KEY = "ticket_12306:cookies:v1"
_REFRESH_LOCK_KEY = "ticket_12306:cookies:refresh_lock"
_INIT_URL = "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc"

# 12306 RAIL_EXPIRATION cookies typically last several hours; we proactively
# refresh well before that to keep traffic healthy.
DEFAULT_COOKIE_TTL_SECONDS = 1500  # 25 minutes
_REFRESH_LOCK_TTL_SECONDS = 30


@dataclass(frozen=True)
class CookieBundle:
    cookies: dict[str, str]
    user_agent: str
    refreshed_at: float


class Ticket12306CookieManager:
    """Manages a shared 12306 cookie set backed by Redis and Playwright.

    Cookies are stored in Redis so multiple API workers share the same
    bootstrapped session. Refresh is guarded by a Redis lock so only one
    worker drives Playwright while others wait and reuse the result.
    """

    def __init__(
        self,
        redis_client: Redis,
        browser_manager: PlaywrightBrowserManager,
        *,
        ttl_seconds: int = DEFAULT_COOKIE_TTL_SECONDS,
        init_url: str = _INIT_URL,
        navigation_timeout_ms: int = 30_000,
    ) -> None:
        self._redis = redis_client
        self._browser_manager = browser_manager
        self._ttl_seconds = ttl_seconds
        self._init_url = init_url
        self._navigation_timeout_ms = navigation_timeout_ms
        self._local_lock = asyncio.Lock()

    async def get(self) -> CookieBundle:
        """Return a usable cookie bundle, refreshing if missing/expired."""
        cached = await self._read_cached()
        if cached is not None:
            return cached
        return await self.refresh_now()

    async def mark_invalid(self) -> None:
        """Drop cached cookies so the next ``get()`` triggers a refresh."""
        try:
            await self._redis.delete(_COOKIE_REDIS_KEY)
        except Exception as exc:  # pragma: no cover - non-fatal
            logger.warning("Failed to invalidate ticket_12306 cookies: %s", exc)

    async def refresh_now(self) -> CookieBundle:
        """Refresh cookies via Playwright, with cross-worker locking."""
        async with self._local_lock:
            # Re-check after acquiring the local lock; another in-process
            # caller may have just refreshed.
            cached = await self._read_cached()
            if cached is not None:
                return cached

            acquired = await self._acquire_refresh_lock()
            if not acquired:
                # Another worker is refreshing; wait briefly and re-read.
                bundle = await self._wait_for_peer_refresh()
                if bundle is not None:
                    return bundle
                # Peer failed to publish in time: fall through and try ourselves.

            try:
                bundle = await self._refresh_via_playwright()
            finally:
                if acquired:
                    await self._release_refresh_lock()

            await self._write_cache(bundle)
            return bundle

    async def _read_cached(self) -> CookieBundle | None:
        try:
            raw = await self._redis.get(_COOKIE_REDIS_KEY)
        except Exception as exc:  # pragma: no cover - non-fatal
            logger.warning("Failed to read ticket_12306 cookies: %s", exc)
            return None
        if not raw:
            return None
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None
        cookies = payload.get("cookies")
        user_agent = payload.get("user_agent")
        refreshed_at = payload.get("refreshed_at")
        if not isinstance(cookies, dict) or not isinstance(user_agent, str):
            return None
        if not isinstance(refreshed_at, (int, float)):
            return None
        return CookieBundle(
            cookies={str(k): str(v) for k, v in cookies.items()},
            user_agent=user_agent,
            refreshed_at=float(refreshed_at),
        )

    async def _write_cache(self, bundle: CookieBundle) -> None:
        payload = {
            "cookies": bundle.cookies,
            "user_agent": bundle.user_agent,
            "refreshed_at": bundle.refreshed_at,
        }
        try:
            await self._redis.setex(
                _COOKIE_REDIS_KEY,
                self._ttl_seconds,
                json.dumps(payload, ensure_ascii=False),
            )
        except Exception as exc:  # pragma: no cover - non-fatal
            logger.warning("Failed to cache ticket_12306 cookies: %s", exc)

    async def _acquire_refresh_lock(self) -> bool:
        try:
            ok = await self._redis.set(
                _REFRESH_LOCK_KEY,
                "1",
                ex=_REFRESH_LOCK_TTL_SECONDS,
                nx=True,
            )
        except Exception as exc:  # pragma: no cover - non-fatal
            logger.warning("Failed to acquire ticket_12306 cookie lock: %s", exc)
            return False
        return bool(ok)

    async def _release_refresh_lock(self) -> None:
        try:
            await self._redis.delete(_REFRESH_LOCK_KEY)
        except Exception as exc:  # pragma: no cover - non-fatal
            logger.warning("Failed to release ticket_12306 cookie lock: %s", exc)

    async def _wait_for_peer_refresh(
        self,
        *,
        max_wait_seconds: float = 10.0,
        poll_interval_seconds: float = 0.3,
    ) -> CookieBundle | None:
        deadline = time() + max_wait_seconds
        while time() < deadline:
            await asyncio.sleep(poll_interval_seconds)
            bundle = await self._read_cached()
            if bundle is not None:
                return bundle
        return None

    async def _refresh_via_playwright(self) -> CookieBundle:
        return await self._browser_manager.run_with_browser(self._collect_cookies)

    async def _collect_cookies(self, browser: Any) -> CookieBundle:
        user_agent = BASE_HEADERS["User-Agent"]
        context = await browser.new_context(
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            user_agent=user_agent,
        )
        try:
            page = await context.new_page()
            page.set_default_timeout(self._navigation_timeout_ms)
            page.set_default_navigation_timeout(self._navigation_timeout_ms)
            try:
                await page.goto(
                    self._init_url,
                    wait_until="domcontentloaded",
                    timeout=self._navigation_timeout_ms,
                )
                await page.wait_for_load_state(
                    "networkidle",
                    timeout=self._navigation_timeout_ms,
                )
            except PlaywrightUnavailableError:
                raise
            except Exception as exc:
                logger.warning(
                    "ticket_12306 init navigation failed: %s; using whatever cookies were set",
                    exc,
                )

            raw_cookies = await context.cookies()
            cookies: dict[str, str] = {}
            for item in raw_cookies or []:
                name = item.get("name")
                value = item.get("value")
                if isinstance(name, str) and isinstance(value, str):
                    cookies[name] = value
        finally:
            await context.close()

        if not cookies:
            logger.warning("ticket_12306 cookie refresh produced no cookies")
        return CookieBundle(
            cookies=cookies,
            user_agent=user_agent,
            refreshed_at=time(),
        )


__all__ = [
    "CookieBundle",
    "DEFAULT_COOKIE_TTL_SECONDS",
    "Ticket12306CookieManager",
]
