"""IP proxy pool with pluggable provider strategy.

Architecture
------------
::

    ProxyProvider (ABC)            ← "从哪里拿代理"
      ├─ StaticProxyProvider       ← 固定列表 (测试/自建)
      ├─ ZhandayeProxyProvider     ← 站大爷 API
      └─ ...                       ← 新厂商只需加一个子类

    ProxyPool                      ← "怎么用代理" (轮询、健康检查、淘汰、补充)

Switching vendors = swap a ProxyProvider implementation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ProxyEntry:
    """A single proxy endpoint."""

    url: str
    """Proxy URL, e.g. ``http://1.2.3.4:8080``."""

    expire_at: float | None = None
    """Monotonic timestamp when proxy expires. None = never expires."""

    # Runtime health tracking (managed by ProxyPool).
    consecutive_failures: int = field(default=0, repr=False)
    last_failure_ts: float = field(default=0.0, repr=False)
    total_requests: int = field(default=0, repr=False)
    total_successes: int = field(default=0, repr=False)

    @property
    def is_expired(self) -> bool:
        if self.expire_at is None:
            return False
        return time.monotonic() >= self.expire_at

    @property
    def is_healthy(self) -> bool:
        return self.consecutive_failures < _MAX_CONSECUTIVE_FAILURES and not self.is_expired


# ---------------------------------------------------------------------------
# Abstract provider interface
# ---------------------------------------------------------------------------


class ProxyProvider(ABC):
    """Strategy interface: how to obtain proxy URLs.

    Implementations handle vendor-specific logic (API keys, auth, formats).
    """

    @abstractmethod
    async def fetch_proxies(self, count: int = 10) -> list[ProxyEntry]:
        """Fetch up to *count* fresh proxy entries from the source.

        Should handle its own errors and return [] on failure.
        """

    async def close(self) -> None:  # noqa: B027
        """Release resources held by the provider."""


# ---------------------------------------------------------------------------
# Built-in provider: static list
# ---------------------------------------------------------------------------


class StaticProxyProvider(ProxyProvider):
    """Provider backed by a fixed list of proxy URLs (for testing/self-managed)."""

    def __init__(self, proxy_urls: list[str]) -> None:
        self._proxy_urls = proxy_urls

    async def fetch_proxies(self, count: int = 10) -> list[ProxyEntry]:
        return [ProxyEntry(url=url) for url in self._proxy_urls[:count]]


# ---------------------------------------------------------------------------
# Built-in provider: 站大爷 (Zhandaye)
# ---------------------------------------------------------------------------


class ZhandayeProxyProvider(ProxyProvider):
    """Provider for 站大爷 (www.zdaye.com / www.zdopen.com) proxy API.

    Parameters
    ----------
    api_url
        Full API URL with auth params, e.g.
        ``http://www.zdopen.com/FreeProxy/Get/?app_id=...&akey=...&dalu=1&return_type=3&count=10``
    proxy_ttl_seconds
        How long each proxy is considered valid. Defaults to 60s for free tier.
        Paid tier may support longer TTL (check vendor docs).
    """

    def __init__(
        self,
        *,
        api_url: str,
        proxy_ttl_seconds: float = 60.0,
    ) -> None:
        self._api_url = api_url
        self._proxy_ttl_seconds = proxy_ttl_seconds
        self._http_client: httpx.AsyncClient | None = None

    async def fetch_proxies(self, count: int = 10) -> list[ProxyEntry]:
        url = self._build_url(count)
        try:
            client = self._get_client()
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("ZhandayeProxyProvider fetch failed: %s", exc)
            return []

        return self._parse_response(response)

    async def close(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient()
        return self._http_client

    def _build_url(self, count: int) -> str:
        # Replace count in URL if present, otherwise append.
        url = self._api_url
        if "count=" in url:
            # Replace existing count value
            import re

            url = re.sub(r"count=\d+", f"count={count}", url)
        else:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}count={count}"
        return url

    def _parse_response(self, response: httpx.Response) -> list[ProxyEntry]:
        try:
            data = response.json()
        except ValueError:
            logger.warning("ZhandayeProxyProvider: non-JSON response")
            return []

        code = data.get("code")
        if code != "10001":
            logger.warning(
                "ZhandayeProxyProvider: unexpected code=%s msg=%s",
                code,
                data.get("msg", ""),
            )
            return []

        proxy_list = data.get("data", {}).get("proxy_list", [])
        if not proxy_list:
            return []

        expire_at = time.monotonic() + self._proxy_ttl_seconds
        entries: list[ProxyEntry] = []
        for item in proxy_list:
            protocol = str(item.get("protocol", "http")).lower()
            # Only use HTTP proxies (skip socks4/socks5).
            if protocol not in ("http", "https"):
                continue
            ip = item.get("ip", "")
            port = item.get("port", "")
            if not ip or not port:
                continue
            proxy_url = f"http://{ip}:{port}"
            entries.append(ProxyEntry(url=proxy_url, expire_at=expire_at))

        logger.info(
            "ZhandayeProxyProvider: got %d HTTP proxies (filtered from %d total)",
            len(entries),
            len(proxy_list),
        )
        return entries


# ---------------------------------------------------------------------------
# Proxy Pool
# ---------------------------------------------------------------------------

_MAX_CONSECUTIVE_FAILURES = 3
_REPLENISH_COOLDOWN_SECONDS = 5.0


class ProxyPool:
    """Manages proxy entries with round-robin, health tracking, and auto-replenish.

    Parameters
    ----------
    provider
        The strategy for fetching new proxies.
    min_pool_size
        When healthy count drops below this, auto-replenish triggers.
    max_pool_size
        Maximum proxies to hold.
    """

    def __init__(
        self,
        *,
        provider: ProxyProvider,
        min_pool_size: int = 3,
        max_pool_size: int = 10,
    ) -> None:
        self._provider = provider
        self._min_pool_size = max(1, min_pool_size)
        self._max_pool_size = max(self._min_pool_size, max_pool_size)
        self._entries: list[ProxyEntry] = []
        self._index = 0
        self._lock = asyncio.Lock()
        self._last_replenish_ts: float = 0.0

    @property
    def healthy_count(self) -> int:
        return sum(1 for e in self._entries if e.is_healthy)

    @property
    def total_count(self) -> int:
        return len(self._entries)

    async def get(self) -> ProxyEntry | None:
        """Get next healthy proxy via round-robin. Returns None if pool empty."""
        self._evict_dead()
        if self.healthy_count < self._min_pool_size:
            await self._replenish()

        healthy = [e for e in self._entries if e.is_healthy]
        if not healthy:
            return None

        self._index = self._index % len(healthy)
        entry = healthy[self._index]
        self._index += 1
        entry.total_requests += 1
        return entry

    def mark_success(self, entry: ProxyEntry) -> None:
        """Record a successful request through the proxy."""
        entry.consecutive_failures = 0
        entry.total_successes += 1

    def mark_failure(self, entry: ProxyEntry) -> None:
        """Record a failed request through the proxy."""
        entry.consecutive_failures += 1
        entry.last_failure_ts = time.monotonic()
        if not entry.is_healthy:
            logger.info(
                "Proxy %s evicted (%d consecutive failures)",
                entry.url,
                entry.consecutive_failures,
            )

    async def warmup(self) -> int:
        """Pre-fill the pool. Returns number of proxies loaded."""
        return await self._replenish(force=True)

    async def close(self) -> None:
        """Release provider resources."""
        await self._provider.close()

    def status(self) -> list[dict[str, Any]]:
        """Snapshot of pool state for diagnostics."""
        return [
            {
                "url": e.url,
                "healthy": e.is_healthy,
                "expired": e.is_expired,
                "failures": e.consecutive_failures,
                "requests": e.total_requests,
                "successes": e.total_successes,
            }
            for e in self._entries
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _evict_dead(self) -> None:
        """Remove expired and unhealthy entries."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.is_healthy]
        evicted = before - len(self._entries)
        if evicted:
            logger.debug("Evicted %d dead/expired proxies", evicted)

    async def _replenish(self, *, force: bool = False) -> int:
        """Fetch new proxies from provider (with cooldown)."""
        now = time.monotonic()
        if not force and now - self._last_replenish_ts < _REPLENISH_COOLDOWN_SECONDS:
            return 0

        async with self._lock:
            # Double-check after acquiring lock.
            if not force and self.healthy_count >= self._min_pool_size:
                return 0
            if (
                not force
                and time.monotonic() - self._last_replenish_ts
                < _REPLENISH_COOLDOWN_SECONDS
            ):
                return 0

            # Remove dead entries first to make room.
            self._entries = [e for e in self._entries if e.is_healthy]
            need = self._max_pool_size - len(self._entries)
            if need <= 0:
                return 0

            self._last_replenish_ts = time.monotonic()
            new_entries = await self._provider.fetch_proxies(count=need)
            if new_entries:
                self._entries.extend(new_entries)
                logger.info(
                    "Proxy pool replenished: +%d (total %d, healthy %d)",
                    len(new_entries),
                    self.total_count,
                    self.healthy_count,
                )
            else:
                logger.warning("Proxy pool replenish returned 0 proxies")
            return len(new_entries)


__all__ = [
    "ProxyEntry",
    "ProxyPool",
    "ProxyProvider",
    "StaticProxyProvider",
    "ZhandayeProxyProvider",
]
