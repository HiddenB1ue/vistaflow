from __future__ import annotations

from abc import ABC, abstractmethod

import httpx


class AbstractGeoClient(ABC):
    """高德地图地理编码客户端抽象基类。"""

    @abstractmethod
    async def geocode_station(
        self, name: str, city: str
    ) -> tuple[float, float] | None:
        """解析站点经纬度，返回 (longitude, latitude) 或 None。"""


class AmapGeoClient(AbstractGeoClient):
    """高德地图 API 真实实现。"""

    GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"

    def __init__(self, api_key: str, http_client: httpx.AsyncClient) -> None:
        self._api_key = api_key
        self._http = http_client

    async def geocode_station(
        self, name: str, city: str
    ) -> tuple[float, float] | None:
        params = {
            "key": self._api_key,
            "address": name,
            "city": city,
            "output": "JSON",
        }
        resp = await self._http.get(
            self.GEOCODE_URL, params=params, timeout=10.0
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1":
            return None
        geocodes = data.get("geocodes", [])
        if not geocodes:
            return None
        location = geocodes[0].get("location", "")
        parts = location.split(",")
        if len(parts) != 2:
            return None
        return float(parts[0]), float(parts[1])


class NullGeoClient(AbstractGeoClient):
    """空实现：未配置高德 API Key 时使用。"""

    async def geocode_station(
        self, name: str, city: str
    ) -> tuple[float, float] | None:
        return None
