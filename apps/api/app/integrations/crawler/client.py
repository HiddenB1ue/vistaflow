from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

STATION_SOURCE_URL = "https://www.12306.cn/index/script/core/common/station_name_new_v10107.js"
STATION_PATTERN = re.compile(r"var\s+station_names\s*=\s*'(.*?)';", re.S)
TRAIN_SEARCH_URL = "https://search.12306.cn/search/v1/train/search"
TRAIN_STOPS_URL = "https://kyfw.12306.cn/otn/queryTrainInfo/query"

CRAWL_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Origin": "https://kyfw.12306.cn",
    "Referer": "https://kyfw.12306.cn/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


class AbstractCrawlerClient(ABC):
    """12306 数据抓取客户端抽象基类。"""

    @abstractmethod
    async def fetch_stations(self) -> list[dict[str, Any]]:
        """抓取全国车站基础数据。"""

    @abstractmethod
    async def fetch_trains(self, date: str, keyword: str) -> list[dict[str, Any]]:
        """按日期和关键字抓取车次目录。"""

    @abstractmethod
    async def fetch_train_stops(self, train_no: str, date: str) -> list[dict[str, Any]]:
        """抓取指定 train_no 在某天的经停明细。"""

    @abstractmethod
    async def fetch_train_runs(self, date: str, train_code: str) -> list[dict[str, Any]]:
        """抓取指定日期与车次对应的运行候选数据。"""

    async def fetch_train_status(self, date: str, train_code: str) -> list[dict[str, Any]]:
        return await self.fetch_train_runs(date, train_code)


class Live12306CrawlerClient(AbstractCrawlerClient):
    """真实 12306 HTTP 客户端实现。"""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client

    async def fetch_stations(self) -> list[dict[str, Any]]:
        response = await self._request_text(STATION_SOURCE_URL)
        match = STATION_PATTERN.search(response)
        if not match:
            raise RuntimeError("station_names not found in source")

        stations: list[dict[str, Any]] = []
        for raw_item in match.group(1).split("@"):
            if not raw_item:
                continue
            parts = raw_item.split("|")
            if len(parts) != 11:
                continue
            stations.append(
                {
                    "telecode": parts[2],
                    "name": parts[1],
                    "pinyin": parts[3],
                    "abbr": parts[4],
                    "area_code": parts[6],
                    "area_name": parts[7],
                    "country_code": parts[8] or "cn",
                    "country_name": parts[9] or "中国",
                }
            )
        return stations

    async def fetch_trains(self, date: str, keyword: str) -> list[dict[str, Any]]:
        compact_date = _normalize_search_date(date)
        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            raise ValueError("keyword cannot be empty")

        payload = await self._request_json(
            TRAIN_SEARCH_URL,
            params={"keyword": cleaned_keyword, "date": compact_date},
        )
        if not payload.get("status"):
            raise RuntimeError(str(payload.get("errorMsg") or "search failed"))

        rows = payload.get("data")
        if not isinstance(rows, list):
            return []

        normalized: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized.append(
                {
                    "run_date": _normalize_iso_date(date),
                    "date": compact_date,
                    "train_no": str(row.get("train_no") or "").strip(),
                    "station_train_code": str(
                        row.get("station_train_code") or ""
                    ).strip(),
                    "from_station": _normalize_station_name(row.get("from_station")),
                    "to_station": _normalize_station_name(row.get("to_station")),
                    "total_num": _to_int(row.get("total_num")),
                    "data_flag": row.get("data"),
                    "keyword": cleaned_keyword,
                }
            )
        return normalized

    async def fetch_train_stops(self, train_no: str, date: str) -> list[dict[str, Any]]:
        normalized_date = _normalize_iso_date(date)
        payload = await self._request_json(
            TRAIN_STOPS_URL,
            params={
                "leftTicketDTO.train_no": train_no,
                "leftTicketDTO.train_date": normalized_date,
                "rand_code": "",
            },
        )
        if not payload.get("status"):
            raise RuntimeError(f"queryTrainInfo failed: train_no={train_no}")

        data_payload = payload.get("data")
        if not isinstance(data_payload, dict):
            return []
        rows = data_payload.get("data")
        if not isinstance(rows, list):
            return []

        normalized: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized.append(
                {
                    "train_no": train_no,
                    "train_date": normalized_date,
                    "station_no": _to_int(row.get("station_no")),
                    "station_name": row.get("station_name"),
                    "station_train_code": row.get("station_train_code"),
                    "arrive_time": row.get("arrive_time"),
                    "start_time": row.get("start_time"),
                    "running_time": row.get("running_time"),
                    "arrive_day_diff": _to_int(row.get("arrive_day_diff")),
                    "arrive_day_str": row.get("arrive_day_str"),
                    "is_start": row.get("is_start"),
                    "start_station_name": row.get("start_station_name"),
                    "end_station_name": row.get("end_station_name"),
                    "train_class_name": row.get("train_class_name"),
                    "service_type": row.get("service_type"),
                    "wz_num": row.get("wz_num"),
                }
            )
        return normalized

    async def fetch_train_runs(self, date: str, train_code: str) -> list[dict[str, Any]]:
        return await self.fetch_trains(date, train_code)

    async def _request_json(self, url: str, *, params: dict[str, str]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = await self._http.get(
                    url,
                    params=params,
                    headers=CRAWL_HEADERS,
                    timeout=20.0,
                    follow_redirects=False,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise RuntimeError("unexpected response payload")
                return payload
            except Exception as exc:  # pragma: no cover
                last_error = exc
                if attempt >= 3:
                    break
                await asyncio.sleep(0.2 * attempt)
        raise RuntimeError(f"12306 request failed: {last_error}") from last_error

    async def _request_text(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = await self._http.get(url, timeout=30.0)
                response.raise_for_status()
                return response.text
            except Exception as exc:  # pragma: no cover
                last_error = exc
                if attempt >= 3:
                    break
                await asyncio.sleep(0.2 * attempt)
        raise RuntimeError(f"12306 request failed: {last_error}") from last_error


class NullCrawlerClient(AbstractCrawlerClient):
    """空实现：未配置爬虫时使用。"""

    async def fetch_stations(self) -> list[dict[str, Any]]:
        return []

    async def fetch_trains(self, date: str, keyword: str) -> list[dict[str, Any]]:
        return []

    async def fetch_train_stops(self, train_no: str, date: str) -> list[dict[str, Any]]:
        return []

    async def fetch_train_runs(self, date: str, train_code: str) -> list[dict[str, Any]]:
        return []


def _normalize_search_date(raw: str) -> str:
    text = raw.strip()
    if len(text) == 8 and text.isdigit():
        return text
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return f"{text[:4]}{text[5:7]}{text[8:10]}"
    raise ValueError("date must be YYYY-MM-DD or YYYYMMDD")


def _normalize_iso_date(raw: str) -> str:
    text = raw.strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    raise ValueError("date must be YYYY-MM-DD or YYYYMMDD")


def _normalize_station_name(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def _to_int(value: Any) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None
