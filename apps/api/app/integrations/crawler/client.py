from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx


class AbstractCrawlerClient(ABC):
    """12306 数据爬取客户端抽象基类。"""

    @abstractmethod
    async def fetch_stations(self) -> list[dict[str, Any]]:
        """抓取全国车站基础数据。"""

    @abstractmethod
    async def fetch_train_status(
        self, date: str, train_code: str
    ) -> list[dict[str, Any]]:
        """抓取车次运行状态。"""


class Live12306CrawlerClient(AbstractCrawlerClient):
    """真实 12306 HTTP 客户端实现。"""

    STATION_URL = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client

    async def fetch_stations(self) -> list[dict[str, Any]]:
        resp = await self._http.get(self.STATION_URL, timeout=30.0)
        resp.raise_for_status()
        text = resp.text
        # 解析 station_name.js 格式: var station_names='@bjb|北京北|VAP|...'
        start = text.find("'")
        end = text.rfind("'")
        if start == -1 or end == -1 or start >= end:
            return []
        raw = text[start + 1 : end]
        stations: list[dict[str, Any]] = []
        for entry in raw.split("@"):
            if not entry.strip():
                continue
            parts = entry.split("|")
            if len(parts) >= 5:
                stations.append(
                    {
                        "abbr": parts[0],
                        "name": parts[1],
                        "telecode": parts[2],
                        "pinyin": parts[3],
                        "area_code": parts[4] if len(parts) > 4 else "",
                    }
                )
        return stations

    async def fetch_train_status(
        self, date: str, train_code: str
    ) -> list[dict[str, Any]]:
        # Placeholder: real implementation would query 12306 train status API
        return []


class NullCrawlerClient(AbstractCrawlerClient):
    """空实现：未配置爬虫时使用。"""

    async def fetch_stations(self) -> list[dict[str, Any]]:
        return []

    async def fetch_train_status(
        self, date: str, train_code: str
    ) -> list[dict[str, Any]]:
        return []
