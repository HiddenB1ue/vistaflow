from __future__ import annotations

import asyncio
import json
import logging
from time import time
from typing import Any

from redis.asyncio import Redis

from app.integrations.ticket_12306.browser_manager import (
    PlaywrightBrowserManager,
    PlaywrightUnavailableError,
)
from app.integrations.ticket_12306.cookie_manager import (
    DEFAULT_COOKIE_TTL_SECONDS,
    CookieBundle,
)
from app.integrations.ticket_12306.parser import BASE_HEADERS

logger = logging.getLogger(__name__)

_SLOT_KEY_PREFIX = "ticket_12306:cookie_pool:slot:"
_INIT_URL = "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc"


class CookiePool:
    """Pool of N independent 12306 cookie sessions stored in Redis.

    Each slot holds a separate :class:`CookieBundle` with its own TTL.
    ``get()`` round-robins through available slots.  When a request fails,
    ``mark_invalid(bundle)`` removes the offending slot so subsequent calls
    skip it or trigger a Playwright refresh.

    Call ``refresh_pool()`` periodically from a background task to keep slots
    warm.  Each refresh opens a fresh Playwright browser context, which is
    independent of other slots.
    """

    def __init__(
        self,
        redis_client: Redis,
        browser_manager: PlaywrightBrowserManager,
        *,
        pool_size: int = 3,
        ttl_seconds: int = DEFAULT_COOKIE_TTL_SECONDS,
        init_url: str = _INIT_URL,
        navigation_timeout_ms: int = 30_000,
    ) -> None:
        self._redis = redis_client
        self._browser_manager = browser_manager
        self._pool_size = pool_size
        self._ttl_seconds = ttl_seconds
        self._init_url = init_url
        self._navigation_timeout_ms = navigation_timeout_ms
        self._counter = 0
        self._lock = asyncio.Lock()

    @property
    def pool_size(self) -> int:
        return self._pool_size

    # ------------------------------------------------------------------
    # Public interface (compatible with Ticket12306CookieManager shape)
    # ------------------------------------------------------------------

    async def get(self) -> CookieBundle:
        """Return a usable cookie bundle, round-robin across pool slots.

        If every slot is empty after a full rotation, one slot is refreshed
        synchronously before returning.
        """
        async with self._lock:
            for _ in range(self._pool_size):
                slot_id = self._counter % self._pool_size
                self._counter += 1
                bundle = await self._read_slot(slot_id)
                if bundle is not None:
                    return bundle

        # All slots empty — refresh slot 0 as last resort
        return await self._refresh_single_slot(0)

    async def mark_invalid(self, bundle: CookieBundle | None = None) -> None:
        """Invalidate the slot associated with *bundle*.

        If *bundle* is ``None`` or has no ``slot_id``, the call is a no-op so
        that callers do not need to guard.
        """
        if bundle is not None and bundle.slot_id >= 0:
            try:
                await self._redis.delete(self._slot_key(bundle.slot_id))
                logger.info("Cookie pool slot %d invalidated", bundle.slot_id)
            except Exception as exc:
                logger.warning(
                    "Failed to invalidate cookie pool slot %d: %s",
                    bundle.slot_id,
                    exc,
                )

    # ------------------------------------------------------------------
    # Background maintenance
    # ------------------------------------------------------------------

    async def refresh_pool(self) -> int:
        """Refresh all empty / expired slots.  Returns number refreshed."""
        empty_slots: list[int] = []
        for i in range(self._pool_size):
            bundle = await self._read_slot(i)
            if bundle is None:
                empty_slots.append(i)

        if not empty_slots:
            return 0

        logger.info(
            "Cookie pool: refreshing %d/%d empty slots",
            len(empty_slots),
            self._pool_size,
        )

        async def _refresh_one(slot_id: int) -> bool:
            try:
                await self._refresh_single_slot(slot_id)
                return True
            except Exception as exc:
                logger.warning(
                    "Cookie pool: failed to refresh slot %d: %s", slot_id, exc
                )
                return False

        results = await asyncio.gather(
            *(_refresh_one(sid) for sid in empty_slots)
        )
        refreshed = sum(1 for ok in results if ok)
        logger.info("Cookie pool: refreshed %d slots", refreshed)
        return refreshed

    async def status(self) -> list[dict[str, Any]]:
        """Diagnostic info for each slot (admin / debug endpoint)."""
        slots: list[dict[str, Any]] = []
        for i in range(self._pool_size):
            bundle = await self._read_slot(i)
            slots.append({
                "slot_id": i,
                "valid": bundle is not None,
                "refreshed_at": bundle.refreshed_at if bundle else None,
                "age_seconds": (
                    round(time() - bundle.refreshed_at, 1) if bundle else None
                ),
            })
        return slots

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _slot_key(self, slot_id: int) -> str:
        return f"{_SLOT_KEY_PREFIX}{slot_id}"

    async def _read_slot(self, slot_id: int) -> CookieBundle | None:
        try:
            raw = await self._redis.get(self._slot_key(slot_id))
        except Exception as exc:
            logger.warning("Cookie pool: read slot %d failed: %s", slot_id, exc)
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
            slot_id=slot_id,
        )

    async def _write_slot(self, slot_id: int, bundle: CookieBundle) -> None:
        payload = {
            "cookies": bundle.cookies,
            "user_agent": bundle.user_agent,
            "refreshed_at": bundle.refreshed_at,
        }
        try:
            await self._redis.setex(
                self._slot_key(slot_id),
                self._ttl_seconds,
                json.dumps(payload, ensure_ascii=False),
            )
        except Exception as exc:
            logger.warning("Cookie pool: write slot %d failed: %s", slot_id, exc)

    async def _refresh_single_slot(self, slot_id: int) -> CookieBundle:
        """Mint a fresh cookie via Playwright and store it in *slot_id*."""
        raw = await self._browser_manager.run_with_browser(self._collect_cookies)
        bundle = CookieBundle(
            cookies=raw.cookies,
            user_agent=raw.user_agent,
            refreshed_at=raw.refreshed_at,
            slot_id=slot_id,
        )
        await self._write_slot(slot_id, bundle)
        logger.info("Cookie pool: slot %d refreshed", slot_id)
        return bundle

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
                    "Cookie pool: init navigation failed: %s; "
                    "using whatever cookies were set",
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
            logger.warning("Cookie pool: refresh produced no cookies")
        return CookieBundle(
            cookies=cookies,
            user_agent=user_agent,
            refreshed_at=time(),
        )


__all__ = ["CookiePool"]
