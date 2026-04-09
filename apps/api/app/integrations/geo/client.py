from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio

import httpx


class GeoRateLimitError(RuntimeError):
    """Raised when the upstream geocoder rate-limits requests."""


class GeoAuthError(RuntimeError):
    """Raised when the upstream geocoder key is invalid or unavailable."""


class AbstractGeoClient(ABC):
    """高德地图地理编码客户端抽象基类。"""

    @abstractmethod
    async def geocode_address(
        self, address: str
    ) -> tuple[float, float] | None:
        """解析地址经纬度，返回 (longitude, latitude) 或 None。"""

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the client is backed by a configured upstream service."""

    async def geocode_station(
        self, name: str, city: str | None = None
    ) -> tuple[float, float] | None:
        return await self.geocode_address(name)


class AmapGeoClient(AbstractGeoClient):
    """高德地图 API 真实实现。"""

    GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
    RATE_LIMIT_INFOCODE = "10021"
    AUTH_INFOCODES = {"10001", "10002", "10003", "10004", "10009"}

    def __init__(
        self,
        api_key: str,
        http_client: httpx.AsyncClient,
        *,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        min_interval_seconds: float = 0.35,
        rate_limit_cooldown_seconds: float = 3.0,
    ) -> None:
        self._api_key = api_key
        self._http = http_client
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._min_interval_seconds = max(0.0, min_interval_seconds)
        self._rate_limit_cooldown_seconds = max(0.0, rate_limit_cooldown_seconds)
        self._request_lock = asyncio.Lock()
        self._next_request_at = 0.0

    def is_configured(self) -> bool:
        return True

    async def geocode_address(
        self, address: str
    ) -> tuple[float, float] | None:
        params = {
            "key": self._api_key,
            "address": address,
            "output": "JSON",
        }
        for attempt in range(self._max_retries):
            await self._wait_for_request_slot()
            resp = await self._http.get(
                self.GEOCODE_URL, params=params, timeout=10.0
            )
            resp.raise_for_status()
            data = resp.json()
            status = str(data.get("status", ""))
            if status == "1":
                geocodes = data.get("geocodes", [])
                if not geocodes:
                    return None
                location = geocodes[0].get("location", "")
                parts = location.split(",")
                if len(parts) != 2:
                    return None
                return float(parts[0]), float(parts[1])

            infocode = str(data.get("infocode", ""))
            info = str(data.get("info", "未知错误"))
            if infocode in self.AUTH_INFOCODES:
                raise GeoAuthError(info)
            if infocode == self.RATE_LIMIT_INFOCODE:
                if attempt >= self._max_retries - 1:
                    raise GeoRateLimitError(info)
                backoff_seconds = max(
                    self._rate_limit_cooldown_seconds,
                    self._retry_delay_seconds * (2**attempt),
                )
                await self._push_back_request_slot(backoff_seconds)
                await asyncio.sleep(backoff_seconds)
                continue
            return None

        return None

    async def _wait_for_request_slot(self) -> None:
        if self._min_interval_seconds <= 0:
            return

        loop = asyncio.get_running_loop()
        async with self._request_lock:
            now = loop.time()
            wait_seconds = max(0.0, self._next_request_at - now)
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._next_request_at = loop.time() + self._min_interval_seconds

    async def _push_back_request_slot(self, delay_seconds: float) -> None:
        if delay_seconds <= 0:
            return

        loop = asyncio.get_running_loop()
        async with self._request_lock:
            self._next_request_at = max(self._next_request_at, loop.time() + delay_seconds)


class NullGeoClient(AbstractGeoClient):
    """空实现：未配置高德 API Key 时使用。"""

    async def geocode_address(
        self, address: str
    ) -> tuple[float, float] | None:
        return None

    def is_configured(self) -> bool:
        return False
