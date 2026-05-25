"""Standalone 12306 batch query script.

This script does not use Scrapling's Spider framework. Concurrency is created
by Python's asyncio.gather(), while Scrapling is only used for FetcherSession.

This simplified version does not save CSV files and does not parse response
bodies. It only sends requests and records basic HTTP-level results.
"""

import asyncio
from http.cookies import SimpleCookie
from itertools import permutations
from pathlib import Path
import time

from scrapling.fetchers import FetcherSession


CONCURRENCY = 10
REQUESTS_PER_WORKER = 100
RETRIES = 1
PAUSE_EVERY_REQUESTS = 10
PAUSE_SECONDS = 1

STATIONS_FILE = Path("station_telecodes_100.txt")

INIT_URL = "https://kyfw.12306.cn/otn/leftTicket/init"
QUERY_URL = "https://kyfw.12306.cn/otn/leftTicket/queryG"

BASE_QUERY_PARAMS = {
    "leftTicketDTO.train_date": "2026-05-30",
}

HEADERS = {
    "Referer": INIT_URL,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def load_station_codes() -> list[str]:
    station_codes = [
        line.strip()
        for line in STATIONS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    unique_station_codes = list(dict.fromkeys(station_codes))
    if len(unique_station_codes) < 2:
        raise ValueError(f"{STATIONS_FILE} must contain at least two station telecodes.")

    return unique_station_codes


def build_station_pairs(station_codes: list[str]) -> list[tuple[str, str]]:
    required_pairs = CONCURRENCY * REQUESTS_PER_WORKER
    station_pairs = list(permutations(station_codes, 2))
    if len(station_pairs) < required_pairs:
        raise ValueError(
            f"Not enough station pairs. Need {required_pairs}, got {len(station_pairs)} "
            f"from {len(station_codes)} stations."
        )

    return station_pairs


def build_query_params(from_station: str, to_station: str) -> dict[str, str]:
    return {
        **BASE_QUERY_PARAMS,
        "leftTicketDTO.from_station": from_station,
        "leftTicketDTO.to_station": to_station,
        "purpose_codes": "ADULT",
    }


def parse_set_cookie(set_cookie_header: str | None) -> dict[str, str]:
    cookie = SimpleCookie()
    cookie.load(set_cookie_header or "")
    return {key: morsel.value for key, morsel in cookie.items()}


def build_cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in cookies.items())


def build_headers(cookies: dict[str, str] | None = None) -> dict[str, str]:
    if not cookies:
        return dict(HEADERS)

    return {
        **HEADERS,
        "Cookie": build_cookie_header(cookies),
        "Origin": "https://kyfw.12306.cn",
        "X-Requested-With": "XMLHttpRequest",
    }


def is_successful_response(page) -> bool:
    return page.status == 200


async def worker(worker_id: int, station_pairs: list[tuple[str, str]]) -> dict[str, int]:
    stats = {"ok": 0, "failed": 0, "exceptions": 0}

    try:
        async with FetcherSession(impersonate="chrome", stealthy_headers=True, timeout=30, retries=RETRIES) as session:
            init = await session.get(
                INIT_URL,
                headers=HEADERS,
                follow_redirects=False,
                timeout=30,
                retries=RETRIES,
            )
            cookies = parse_set_cookie(init.headers.get("set-cookie"))
            headers = build_headers(cookies)
            print(f"worker={worker_id} init: status={init.status} url={init.url}")

            for request_id in range(REQUESTS_PER_WORKER):
                pair_index = worker_id * REQUESTS_PER_WORKER + request_id
                from_station, to_station = station_pairs[pair_index]

                try:
                    page = await session.get(
                        QUERY_URL,
                        params=build_query_params(from_station, to_station),
                        headers=headers,
                        follow_redirects=False,
                        timeout=30,
                        retries=RETRIES,
                    )
                    if is_successful_response(page):
                        stats["ok"] += 1
                    else:
                        stats["failed"] += 1
                        print(
                            f"worker={worker_id} request={request_id} failed "
                            f"route={from_station}->{to_station} "
                            f"status={page.status} url={page.url} "
                            f"content_type={page.headers.get('content-type', '')}"
                        )
                except Exception as exc:
                    stats["exceptions"] += 1
                    print(
                        f"worker={worker_id} request={request_id} "
                        f"route={from_station}->{to_station} exception={type(exc).__name__}: {exc}"
                    )

                completed_requests = request_id + 1
                if completed_requests < REQUESTS_PER_WORKER and completed_requests % PAUSE_EVERY_REQUESTS == 0:
                    await asyncio.sleep(PAUSE_SECONDS)
    except Exception as exc:
        stats["exceptions"] += REQUESTS_PER_WORKER
        print(f"worker={worker_id} setup exception={type(exc).__name__}: {exc}")

    return stats


async def main() -> None:
    station_codes = load_station_codes()
    station_pairs = build_station_pairs(station_codes)
    planned_requests = CONCURRENCY * REQUESTS_PER_WORKER
    print(
        f"loaded_stations={len(station_codes)} unique_pairs={len(station_pairs)} "
        f"planned_requests={planned_requests}"
    )

    started_at = time.perf_counter()
    results = await asyncio.gather(*(worker(worker_id, station_pairs) for worker_id in range(CONCURRENCY)))
    elapsed = time.perf_counter() - started_at

    ok = sum(item["ok"] for item in results)
    failed = sum(item["failed"] for item in results)
    exceptions = sum(item["exceptions"] for item in results)
    total = ok + failed + exceptions

    print("total:", total)
    print("ok:", ok)
    print("failed:", failed)
    print("exceptions:", exceptions)
    print("elapsed:", round(elapsed, 2), "s")
    print("rps:", round(total / elapsed, 2) if elapsed else 0)


if __name__ == "__main__":
    asyncio.run(main())
