from __future__ import annotations

import asyncio
import time

from app.integrations.ticket_12306.proxy_pool import (
    ProxyEntry,
    ProxyPool,
    ProxyProvider,
    StaticProxyProvider,
    ZhandayeProxyProvider,
)

# ---------------------------------------------------------------------------
# ProxyEntry
# ---------------------------------------------------------------------------


def test_proxy_entry_never_expires_when_no_expire_at() -> None:
    entry = ProxyEntry(url="http://1.2.3.4:8080")
    assert not entry.is_expired
    assert entry.is_healthy


def test_proxy_entry_expires_when_past_deadline() -> None:
    entry = ProxyEntry(url="http://1.2.3.4:8080", expire_at=time.monotonic() - 1)
    assert entry.is_expired
    assert not entry.is_healthy


def test_proxy_entry_unhealthy_after_3_failures() -> None:
    entry = ProxyEntry(url="http://1.2.3.4:8080")
    entry.consecutive_failures = 2
    assert entry.is_healthy
    entry.consecutive_failures = 3
    assert not entry.is_healthy


# ---------------------------------------------------------------------------
# StaticProxyProvider
# ---------------------------------------------------------------------------


def test_static_provider_returns_entries() -> None:
    urls = ["http://a:1", "http://b:2", "http://c:3"]
    provider = StaticProxyProvider(urls)
    entries = asyncio.run(provider.fetch_proxies(count=2))
    assert len(entries) == 2
    assert entries[0].url == "http://a:1"
    assert entries[1].url == "http://b:2"
    assert entries[0].expire_at is None


# ---------------------------------------------------------------------------
# ZhandayeProxyProvider._parse_response
# ---------------------------------------------------------------------------


def test_zhandaye_parse_filters_non_http() -> None:
    import httpx

    provider = ZhandayeProxyProvider(
        api_url="http://example.com",
        proxy_ttl_seconds=30.0,
    )
    body = {
        "code": "10001",
        "msg": "ok",
        "data": {
            "count": 4,
            "proxy_list": [
                {"ip": "1.1.1.1", "port": 8080, "protocol": "http", "level": "高匿"},
                {"ip": "2.2.2.2", "port": 1080, "protocol": "socks5", "level": "高匿"},
                {"ip": "3.3.3.3", "port": 443, "protocol": "https", "level": "高匿"},
                {"ip": "4.4.4.4", "port": 1081, "protocol": "socks4", "level": "高匿"},
            ],
        },
    }
    response = httpx.Response(200, json=body)
    entries = provider._parse_response(response)
    # Only http and https should pass, socks4/socks5 filtered out.
    assert len(entries) == 2
    assert entries[0].url == "http://1.1.1.1:8080"
    assert entries[1].url == "http://3.3.3.3:443"
    assert entries[0].expire_at is not None


def test_zhandaye_parse_handles_bad_code() -> None:
    import httpx

    provider = ZhandayeProxyProvider(api_url="http://example.com")
    body = {"code": "10002", "msg": "fail", "data": {}}
    response = httpx.Response(200, json=body)
    entries = provider._parse_response(response)
    assert entries == []


# ---------------------------------------------------------------------------
# ProxyPool
# ---------------------------------------------------------------------------


class CountingProvider(ProxyProvider):
    """Provider that generates numbered proxies and counts calls."""

    def __init__(self) -> None:
        self.call_count = 0

    async def fetch_proxies(self, count: int = 10) -> list[ProxyEntry]:
        self.call_count += 1
        return [
            ProxyEntry(url=f"http://proxy-{self.call_count}-{i}:8080")
            for i in range(count)
        ]


def test_pool_get_returns_proxy_after_warmup() -> None:
    provider = CountingProvider()
    pool = ProxyPool(provider=provider, min_pool_size=2, max_pool_size=5)
    asyncio.run(pool.warmup())
    assert pool.healthy_count == 5
    entry = asyncio.run(pool.get())
    assert entry is not None
    assert entry.url.startswith("http://proxy-")


def test_pool_round_robin() -> None:
    provider = CountingProvider()
    pool = ProxyPool(provider=provider, min_pool_size=2, max_pool_size=3)
    asyncio.run(pool.warmup())
    urls = [asyncio.run(pool.get()).url for _ in range(6)]  # type: ignore[union-attr]
    # Should cycle through all 3 proxies twice.
    assert urls[0] == urls[3]
    assert urls[1] == urls[4]
    assert urls[2] == urls[5]


def test_pool_mark_failure_evicts_unhealthy() -> None:
    provider = CountingProvider()
    pool = ProxyPool(provider=provider, min_pool_size=1, max_pool_size=3)
    asyncio.run(pool.warmup())
    entry = asyncio.run(pool.get())
    assert entry is not None
    # Mark 3 consecutive failures → proxy becomes unhealthy.
    pool.mark_failure(entry)
    pool.mark_failure(entry)
    pool.mark_failure(entry)
    assert not entry.is_healthy
    # Pool should have 2 healthy remaining.
    assert pool.healthy_count == 2


def test_pool_mark_success_resets_failures() -> None:
    entry = ProxyEntry(url="http://x:1")
    entry.consecutive_failures = 2
    provider = CountingProvider()
    pool = ProxyPool(provider=provider, min_pool_size=1, max_pool_size=3)
    pool.mark_success(entry)
    assert entry.consecutive_failures == 0
    assert entry.total_successes == 1


def test_pool_returns_none_when_empty_provider() -> None:
    class EmptyProvider(ProxyProvider):
        async def fetch_proxies(self, count: int = 10) -> list[ProxyEntry]:
            return []

    pool = ProxyPool(provider=EmptyProvider(), min_pool_size=1, max_pool_size=3)
    result = asyncio.run(pool.get())
    assert result is None


def test_pool_status_snapshot() -> None:
    provider = CountingProvider()
    pool = ProxyPool(provider=provider, min_pool_size=1, max_pool_size=2)
    asyncio.run(pool.warmup())
    status = pool.status()
    assert len(status) == 2
    assert all(s["healthy"] for s in status)
    assert all(s["failures"] == 0 for s in status)
