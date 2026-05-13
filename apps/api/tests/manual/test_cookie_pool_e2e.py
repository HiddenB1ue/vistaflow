"""Manual end-to-end test: fetch all leg prices for 北京→上海 on 2026-05-20.

Usage:
    cd apps/api
    uv run python -m tests.manual.test_cookie_pool_e2e
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from datetime import date
from typing import Any

import asyncpg
import redis.asyncio as aioredis

from app.integrations.ticket_12306.browser_manager import PlaywrightBrowserManager
from app.integrations.ticket_12306.cookie_pool import CookiePool
from app.integrations.ticket_12306.http_client import HttpTicketClient, TicketHttpFailure
from app.integrations.ticket_12306.proxy_pool import ProxyPool, ZhandayeProxyProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("e2e-test")

DB_DSN = "postgresql://vistaflow:vistaflow@localhost:5432/vistaflow"
REDIS_URL = "redis://localhost:6379/2"
RUN_DATE = "2026-05-20"
FROM_STATION = "北京"
TO_STATION = "上海"

# 站大爷 proxy API (set to empty string to disable proxy pool)
PROXY_API_URL = (
    # Disabled: free proxies don't support HTTPS CONNECT for 12306.
    # "http://www.zdopen.com/FreeProxy/Get/"
    # "?app_id=202605121326094118&akey=cca983869f76b021&dalu=1&return_type=3&count=10"
    ""
)
PROXY_TTL_SECONDS = 60.0


async def get_legs_from_db(
    pool: asyncpg.Pool,
) -> list[dict[str, Any]]:
    """Load unique legs and their telecodes from route_plan_segment."""
    # Find the plan
    plan = await pool.fetchrow(
        "SELECT plan_id FROM route_plan_cache "
        "WHERE from_station = $1 AND to_station = $2 AND search_date = $3 "
        "ORDER BY created_at DESC LIMIT 1",
        FROM_STATION, TO_STATION, date.fromisoformat(RUN_DATE),
    )
    if not plan:
        logger.error("No plan found for %s→%s on %s", FROM_STATION, TO_STATION, RUN_DATE)
        return []

    plan_id = plan["plan_id"]
    logger.info("Using plan_id: %s", plan_id)

    # Get candidate count
    count = await pool.fetchval(
        "SELECT COUNT(*) FROM route_plan_candidate WHERE plan_id = $1", plan_id
    )
    logger.info("Total candidates: %d", count)

    # Get unique legs from segments
    leg_rows = await pool.fetch(
        "SELECT DISTINCT from_station, to_station "
        "FROM route_plan_segment WHERE plan_id = $1 "
        "ORDER BY from_station, to_station",
        plan_id,
    )
    logger.info("Unique legs in DB: %d", len(leg_rows))

    # Also get all segments with train info for diagnosis
    seg_rows = await pool.fetch(
        "SELECT DISTINCT from_station, to_station, train_no, train_code "
        "FROM route_plan_segment WHERE plan_id = $1 "
        "ORDER BY from_station, to_station, train_code",
        plan_id,
    )
    logger.info("Total unique segments (leg+train): %d", len(seg_rows))
    for sr in seg_rows:
        logger.info(
            "  seg: %s→%s  train_no=%s  code=%s",
            sr["from_station"], sr["to_station"], sr["train_no"], sr["train_code"],
        )

    # Resolve telecodes for all station names
    station_names = set()
    for lr in leg_rows:
        station_names.add(lr["from_station"])
        station_names.add(lr["to_station"])

    telecode_rows = await pool.fetch(
        "SELECT name, telecode FROM stations "
        "WHERE name = ANY($1) AND telecode IS NOT NULL AND telecode <> ''",
        sorted(station_names),
    )
    telecodes = {str(r["name"]): str(r["telecode"]) for r in telecode_rows}
    logger.info("Telecodes resolved: %s", telecodes)

    missing = station_names - set(telecodes.keys())
    if missing:
        logger.warning("Missing telecodes for: %s", missing)

    legs = []
    for lr in leg_rows:
        from_st = lr["from_station"]
        to_st = lr["to_station"]
        from_code = telecodes.get(from_st)
        to_code = telecodes.get(to_st)
        if from_code and to_code:
            legs.append({
                "from_station": from_st,
                "to_station": to_st,
                "from_code": from_code,
                "to_code": to_code,
            })
    return legs


async def main() -> None:
    logger.info("=== Cookie Pool E2E Test ===")
    logger.info("Route: %s → %s  Date: %s", FROM_STATION, TO_STATION, RUN_DATE)

    # 1. Connect
    db_pool = await asyncpg.create_pool(dsn=DB_DSN, min_size=2, max_size=5)
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.ping()
    logger.info("DB and Redis connected")

    # 2. Clear any existing Redis cache for this date to force fresh fetches
    pattern = f"journey_search:ticket_segment:v3:{RUN_DATE}:*"
    cursor = 0
    deleted = 0
    while True:
        cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await redis_client.delete(*keys)
            deleted += len(keys)
        if cursor == 0:
            break
    logger.info("Cleared %d existing Redis cache keys for %s", deleted, RUN_DATE)

    # 3. Load legs from DB
    legs = await get_legs_from_db(db_pool)
    if not legs:
        logger.error("No legs to fetch")
        await db_pool.close()
        await redis_client.aclose()
        return

    logger.info("Legs to fetch: %d", len(legs))
    for leg in legs:
        logger.info(
            "  %s(%s) → %s(%s)",
            leg["from_station"], leg["from_code"],
            leg["to_station"], leg["to_code"],
        )

    # 4. Create CookiePool and warm it up
    browser_manager = PlaywrightBrowserManager()
    cookie_pool = CookiePool(
        redis_client=redis_client,
        browser_manager=browser_manager,
        pool_size=3,
    )

    logger.info("Warming up cookie pool...")
    t0 = time.monotonic()
    refreshed = await cookie_pool.refresh_pool()
    t1 = time.monotonic()
    logger.info("Cookie pool warmed: %d slots in %.1fs", refreshed, t1 - t0)

    status = await cookie_pool.status()
    for s in status:
        logger.info("  slot %d: valid=%s", s["slot_id"], s["valid"])

    # 4b. Create ProxyPool (if configured)
    proxy_pool = None
    if PROXY_API_URL:
        provider = ZhandayeProxyProvider(
            api_url=PROXY_API_URL,
            proxy_ttl_seconds=PROXY_TTL_SECONDS,
        )
        proxy_pool = ProxyPool(provider=provider, min_pool_size=3, max_pool_size=10)
        loaded = await proxy_pool.warmup()
        logger.info("Proxy pool warmed: %d proxies loaded", loaded)
        for ps in proxy_pool.status():
            logger.info("  proxy: %s healthy=%s", ps["url"], ps["healthy"])
    else:
        logger.info("Proxy pool disabled (no PROXY_API_URL)")

    # 5. Fetch each leg via HttpTicketClient
    http_client = HttpTicketClient(
        cookie_pool=cookie_pool,
        proxy_pool=proxy_pool,
        max_concurrency=3,
        jitter_min_seconds=0.2,
        jitter_max_seconds=0.5,
    )

    success_count = 0
    fail_count = 0
    empty_count = 0
    fetch_start = time.monotonic()

    for leg in legs:
        from_station = leg["from_station"]
        to_station = leg["to_station"]
        from_code = leg["from_code"]
        to_code = leg["to_code"]
        t0 = time.monotonic()
        try:
            rows = await http_client.fetch_leg(
                RUN_DATE, from_station, to_station, from_code, to_code
            )
            elapsed = time.monotonic() - t0
            if rows:
                train_count = len(rows)
                # Show a few train details
                sample_trains = list(rows.keys())[:5]
                logger.info(
                    "  OK %s→%s: %d trains (%.1fs) sample=%s",
                    from_station, to_station, train_count, elapsed, sample_trains,
                )
                success_count += 1
            else:
                logger.info(
                    "  EMPTY %s→%s: no trains (%.1fs)",
                    from_station, to_station, elapsed,
                )
                empty_count += 1
        except TicketHttpFailure as exc:
            elapsed = time.monotonic() - t0
            logger.error(
                "  FAIL %s→%s: %s (%.1fs)",
                from_station, to_station, exc, elapsed,
            )
            fail_count += 1
        except Exception as exc:
            elapsed = time.monotonic() - t0
            logger.error(
                "  ERR %s→%s: %s (%.1fs)",
                from_station, to_station, exc, elapsed,
            )
            fail_count += 1

    # 6. Summary
    total_elapsed = time.monotonic() - fetch_start
    total = success_count + fail_count + empty_count
    logger.info("=== Results ===")
    logger.info("  Total legs: %d", total)
    logger.info("  Success:    %d", success_count)
    logger.info("  Empty:      %d", empty_count)
    logger.info("  Failed:     %d", fail_count)
    logger.info("  Total fetch time: %.1fs", total_elapsed)

    pool_status = await cookie_pool.status()
    logger.info("Cookie pool status:")
    for s in pool_status:
        logger.info("  slot %d: valid=%s", s["slot_id"], s["valid"])

    if proxy_pool is not None:
        logger.info("Proxy pool status:")
        for ps in proxy_pool.status():
            logger.info(
                "  %s healthy=%s reqs=%d ok=%d fail=%d",
                ps["url"], ps["healthy"], ps["requests"],
                ps["successes"], ps["failures"],
            )

    # Cleanup
    if proxy_pool is not None:
        await proxy_pool.close()
    await browser_manager.close()
    await db_pool.close()
    await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
