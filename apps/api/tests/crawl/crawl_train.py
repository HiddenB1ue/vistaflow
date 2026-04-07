from __future__ import annotations

import csv
import random
import re
import time
from pathlib import Path
from typing import Any

import httpx

# 12306 车次搜索接口。
SEARCH_URL = "https://search.12306.cn/search/v1/train/search"

# 基础请求头（简化版，避免复杂机制）。
BASE_HEADERS = {
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


def normalize_date(value: str) -> str:
    """将日期标准化为 YYYYMMDD。"""
    text = value.strip()
    if len(text) == 8 and text.isdigit():
        return text
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        y, m, d = text.split("-")
        if y.isdigit() and m.isdigit() and d.isdigit():
            return f"{y}{m}{d}"
    raise ValueError("date must be YYYYMMDD or YYYY-MM-DD")


def normalize_station_name(name: Any) -> str:
    """统一去掉站名中的空白字符，如“合肥 南” -> “合肥南”."""
    return re.sub(r"\s+", "", str(name or ""))


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
        return [f"{keyword}{d}" for d in "123456789"]
    return [f"{keyword}{d}" for d in "0123456789"]


def fetch_by_keyword(
    client: httpx.Client,
    date: str,
    keyword: str,
    max_retries: int,
    retry_sleep_sec: float,
    block_pause_sec: float,
) -> list[dict[str, Any]]:
    """按关键词抓取车次，失败时按和经停脚本一致的退避策略重试。"""
    last_error = "unknown"

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.get(
                SEARCH_URL,
                params={"keyword": keyword, "date": date},
                headers=BASE_HEADERS,
                timeout=20,
            )
            resp.raise_for_status()
            payload: dict[str, Any] = resp.json()
            if not payload.get("status"):
                msg = payload.get("errorMsg") or "unknown error"
                raise RuntimeError(f"12306 search failed: {msg}")
            data = payload.get("data")
            return data if isinstance(data, list) else []
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            last_error = f"HTTPStatus({status_code})"
            if status_code in (403, 429) and attempt < max_retries:
                pause_sec = block_pause_sec * (2 ** (attempt - 1)) + random.uniform(0.0, 5.0)
                print(
                    f"keyword={keyword}: hit {status_code}, pause {pause_sec:.1f}s, "
                    "then retry same keyword."
                )
                time.sleep(pause_sec)
                continue
            if attempt < max_retries:
                time.sleep(retry_sleep_sec * attempt + random.uniform(0.0, 1.0))
                continue
            break
        except httpx.RequestError as exc:
            last_error = exc.__class__.__name__
            if attempt < max_retries:
                time.sleep(retry_sleep_sec * attempt + random.uniform(0.0, 1.0))
                continue
            break
        except Exception as exc:  # pragma: no cover
            last_error = exc.__class__.__name__
            if attempt < max_retries:
                time.sleep(retry_sleep_sec * attempt + random.uniform(0.0, 1.0))
                continue
            break

    raise RuntimeError(f"keyword={keyword}: failed after {max_retries} attempts, last={last_error}")


def crawl_trains(
    date: str,
    result_limit: int,
    expand_span: int,
    max_keyword_length: int,
    max_retries: int,
    retry_sleep_sec: float,
    request_sleep_min_sec: float,
    request_sleep_max_sec: float,
    block_pause_sec: float,
    cooldown_every: int,
    cooldown_sec: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """执行关键词树抓取并返回 (raw_rows, dedup_rows)."""
    visited: set[str] = set()
    keyword_rows: list[tuple[str, list[dict[str, Any]]]] = []
    failed_keywords: list[str] = []
    roots = seed_keywords()
    request_count = 0

    with httpx.Client(
        limits=httpx.Limits(max_connections=5, max_keepalive_connections=2),
        timeout=20.0,
    ) as client:
        for root_index, root in enumerate(roots, start=1):
            if root in visited:
                continue
            print(f"[root] ({root_index}/{len(roots)}) start={root}")
            stack = [root]

            while stack:
                keyword = stack.pop()
                if keyword in visited:
                    continue

                print(f"[crawl] keyword={keyword}")
                rows: list[dict[str, Any]]
                try:
                    rows = fetch_by_keyword(
                        client=client,
                        date=date,
                        keyword=keyword,
                        max_retries=max(1, max_retries),
                        retry_sleep_sec=max(0.0, retry_sleep_sec),
                        block_pause_sec=max(5.0, block_pause_sec),
                    )
                except Exception as exc:
                    failed_keywords.append(keyword)
                    print(f"keyword={keyword}: failed, err={exc}")
                    rows = []

                visited.add(keyword)
                keyword_rows.append((keyword, rows))
                request_count += 1

                expand = should_expand_keyword(
                    keyword=keyword,
                    rows=rows,
                    result_limit=result_limit,
                    expand_span=expand_span,
                    max_keyword_length=max_keyword_length,
                )
                print(
                    f"keyword={keyword}: fetched={len(rows)} "
                    f"last={last_train_code(rows) or '-'} expand={expand}"
                )

                if expand:
                    for child in reversed(expand_keyword(keyword)):
                        if child not in visited:
                            stack.append(child)

                if cooldown_every > 0 and request_count % cooldown_every == 0:
                    cooldown = cooldown_sec + random.uniform(0.0, max(1.0, cooldown_sec * 0.3))
                    print(f"cooldown after {request_count} requests: sleep {cooldown:.1f}s")
                    time.sleep(cooldown)
                else:
                    jitter = random.uniform(request_sleep_min_sec, request_sleep_max_sec)
                    time.sleep(jitter)

    all_rows: list[dict[str, Any]] = []
    for keyword, rows in keyword_rows:
        for row in rows:
            all_rows.append(
                {
                    "date": row.get("date"),
                    "train_no": row.get("train_no"),
                    "station_train_code": row.get("station_train_code"),
                    "from_station": normalize_station_name(row.get("from_station")),
                    "to_station": normalize_station_name(row.get("to_station")),
                    "total_num": row.get("total_num"),
                    "keyword": keyword,
                }
            )

    unique_rows = dedupe_rows(all_rows)
    if failed_keywords:
        print(f"failed keywords: {len(failed_keywords)}")
    return all_rows, unique_rows


def dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按关键字段去重，保留首次出现。"""
    seen: set[tuple[Any, ...]] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in rows:
        key = (
            row.get("date"),
            row.get("train_no"),
            row.get("station_train_code"),
            row.get("from_station"),
            row.get("to_station"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)
    return unique_rows


def dump_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date",
        "train_no",
        "station_train_code",
        "from_station",
        "to_station",
        "total_num",
        "keyword",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    # ===== 手动修改区（按需改这里）=====
    date_input = "2026-03-06"  # 支持 YYYY-MM-DD / YYYYMMDD
    output_csv = Path("test/output/trains_20260306.csv")

    # 关键词扩展策略（越激进越全，但越慢）
    result_limit = 200
    expand_span = 3
    max_keyword_length = 6

    # 请求与重试
    max_retries = 3
    retry_sleep_sec = 1.0
    block_pause_sec = 60.0
    request_sleep_min_sec = 1.2
    request_sleep_max_sec = 2.8
    cooldown_every = 51
    cooldown_sec = 45.0
    # ==================================

    if request_sleep_min_sec > request_sleep_max_sec:
        raise ValueError("request_sleep_min_sec must be <= request_sleep_max_sec")

    date = normalize_date(date_input)
    all_rows, unique_rows = crawl_trains(
        date=date,
        result_limit=result_limit,
        expand_span=expand_span,
        max_keyword_length=max_keyword_length,
        max_retries=max_retries,
        retry_sleep_sec=retry_sleep_sec,
        request_sleep_min_sec=request_sleep_min_sec,
        request_sleep_max_sec=request_sleep_max_sec,
        block_pause_sec=block_pause_sec,
        cooldown_every=cooldown_every,
        cooldown_sec=cooldown_sec,
    )
    dump_csv(unique_rows, output_csv)

    print(f"raw rows: {len(all_rows)}")
    print(f"dedup rows: {len(unique_rows)}")
    print(f"csv output: {output_csv}")
    print("sample:")
    for row in unique_rows[:5]:
        print(row)


if __name__ == "__main__":
    main()
