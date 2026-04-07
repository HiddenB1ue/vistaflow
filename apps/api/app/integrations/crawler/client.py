from __future__ import annotations

import asyncio
import random
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

LETTER_PREFIXES = ("c", "d", "g", "k", "s", "t", "y", "z")
DIGIT_PREFIXES = tuple(str(i) for i in range(10))
RESULT_LIMIT = 200
EXPAND_SPAN = 3
MAX_KEYWORD_LENGTH = 6
MAX_RETRIES = 3
RETRY_SLEEP_SEC = 1.0
BLOCK_PAUSE_SEC = 60.0
REQUEST_SLEEP_MIN_SEC = 1.2
REQUEST_SLEEP_MAX_SEC = 2.8
COOLDOWN_EVERY = 51
COOLDOWN_SEC = 45.0


class TrainSearchFailed(RuntimeError):
    def __init__(self, message: str, *, retry_count: int) -> None:
        super().__init__(message)
        self.retry_count = retry_count


class AbstractCrawlerClient(ABC):
    """12306 数据抓取客户端抽象基类。"""

    @abstractmethod
    async def fetch_stations(self) -> list[dict[str, Any]]:
        """抓取全国车站基础数据。"""

    @abstractmethod
    async def fetch_trains(self, date: str, keyword: str) -> list[dict[str, Any]]:
        """按日期和关键字抓取完整的车次前缀分支。"""

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
        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            raise ValueError("keyword cannot be empty")

        rows: list[dict[str, Any]] = []
        seen_station_train_codes: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = [cleaned_keyword]
        request_count = 0

        while stack:
            current_keyword = stack.pop()
            if current_keyword in visited:
                continue

            batch_rows, _retry_count = await self._fetch_trains_once(date, current_keyword)
            for row in batch_rows:
                station_train_code = str(row.get("station_train_code") or "").strip().upper()
                if not station_train_code or station_train_code in seen_station_train_codes:
                    continue
                seen_station_train_codes.add(station_train_code)
                rows.append(row)
            visited.add(current_keyword)
            request_count += 1
            if should_expand_keyword(
                keyword=current_keyword,
                rows=batch_rows,
                result_limit=RESULT_LIMIT,
                expand_span=EXPAND_SPAN,
                max_keyword_length=MAX_KEYWORD_LENGTH,
            ):
                for child in reversed(expand_keyword(current_keyword)):
                    if child not in visited:
                        stack.append(child)

            if stack:
                await self._sleep_after_request(request_count)

        return rows

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

    async def _fetch_trains_once(
        self,
        date: str,
        keyword: str,
    ) -> tuple[list[dict[str, Any]], int]:
        compact_date = _normalize_search_date(date)
        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            raise ValueError("keyword cannot be empty")

        last_error = "unknown"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self._http.get(
                    TRAIN_SEARCH_URL,
                    params={"keyword": cleaned_keyword, "date": compact_date},
                    headers=CRAWL_HEADERS,
                    timeout=20.0,
                    follow_redirects=False,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise RuntimeError("unexpected response payload")
                if not payload.get("status"):
                    message = str(payload.get("errorMsg") or "search failed")
                    raise RuntimeError(message)
                rows = payload.get("data")
                if not isinstance(rows, list):
                    return [], attempt - 1
                return _normalize_train_rows(rows, date, compact_date, cleaned_keyword), attempt - 1
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                last_error = f"HTTPStatus({status_code})"
                if status_code in (403, 429) and attempt < MAX_RETRIES:
                    pause_sec = BLOCK_PAUSE_SEC * (2 ** (attempt - 1)) + random.uniform(0.0, 5.0)
                    await asyncio.sleep(pause_sec)
                    continue
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_SLEEP_SEC * attempt + random.uniform(0.0, 1.0))
                    continue
                break
            except httpx.RequestError as exc:
                last_error = exc.__class__.__name__
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_SLEEP_SEC * attempt + random.uniform(0.0, 1.0))
                    continue
                break
            except Exception as exc:
                last_error = exc.__class__.__name__
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_SLEEP_SEC * attempt + random.uniform(0.0, 1.0))
                    continue
                break

        raise TrainSearchFailed(
            f"keyword={cleaned_keyword}: failed after {MAX_RETRIES} attempts, last={last_error}",
            retry_count=max(0, MAX_RETRIES - 1),
        )

    async def _sleep_after_request(self, request_count: int) -> None:
        if COOLDOWN_EVERY > 0 and request_count % COOLDOWN_EVERY == 0:
            cooldown = COOLDOWN_SEC + random.uniform(0.0, max(1.0, COOLDOWN_SEC * 0.3))
            await asyncio.sleep(cooldown)
            return
        await asyncio.sleep(random.uniform(REQUEST_SLEEP_MIN_SEC, REQUEST_SLEEP_MAX_SEC))

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


def seed_keywords() -> list[str]:
    return [*LETTER_PREFIXES, *DIGIT_PREFIXES]


def extract_digits(text: str | None) -> str:
    if not text:
        return ""
    match = re.search(r"(\d+)", text)
    return match.group(1) if match else ""


def last_train_code(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    return str(rows[-1].get("station_train_code") or "")


def should_expand_keyword(
    keyword: str,
    rows: list[dict[str, Any]],
    result_limit: int,
    expand_span: int,
    max_keyword_length: int,
) -> bool:
    if len(rows) < result_limit:
        return False
    if len(keyword) >= max_keyword_length:
        return False

    last_digits = extract_digits(last_train_code(rows))
    if not last_digits:
        return False

    keyword_digits = extract_digits(keyword)
    return (len(last_digits) - len(keyword_digits)) >= expand_span


def expand_keyword(keyword: str) -> list[str]:
    if not keyword:
        return []
    if keyword[0].isalpha() and len(keyword) == 1:
        return [f"{keyword}{digit}" for digit in "123456789"]
    return [f"{keyword}{digit}" for digit in "0123456789"]


def _normalize_train_rows(
    rows: list[dict[str, Any]],
    raw_date: str,
    compact_date: str,
    keyword: str,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "run_date": _normalize_iso_date(raw_date),
                "date": compact_date,
                "train_no": str(row.get("train_no") or "").strip(),
                "station_train_code": str(row.get("station_train_code") or "").strip(),
                "from_station": _normalize_station_name(row.get("from_station")),
                "to_station": _normalize_station_name(row.get("to_station")),
                "total_num": _to_int(row.get("total_num")),
                "data_flag": row.get("data"),
                "keyword": keyword,
            }
        )
    return normalized


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
