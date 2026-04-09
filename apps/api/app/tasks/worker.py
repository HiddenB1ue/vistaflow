from __future__ import annotations

import asyncio
import os
import socket
import time
from datetime import UTC, datetime, timedelta

import asyncpg
import httpx

from app.config import get_settings
from app.integrations.crawler.client import Live12306CrawlerClient
from app.integrations.geo.client import DynamicGeoClient
from app.system.constants import SYSTEM_SETTING_CACHE_TTL_SECONDS
from app.system.log_repository import LogRepository
from app.system.settings_provider import SystemSettingsProvider
from app.tasks.registry import create_task_registry
from app.tasks.repository import TaskRepository, TaskRunLogRepository, TaskRunRepository
from app.tasks.runner import TaskRunner


def build_worker_id() -> str:
    return f"{socket.gethostname()}-{os.getpid()}"


async def recover_stale_runs(run_repo: TaskRunRepository, task_repo: TaskRepository) -> None:
    settings = get_settings()
    stale_before = datetime.now(UTC) - timedelta(
        seconds=settings.task_worker_stale_timeout_seconds
    )
    recovered = await run_repo.recover_stale_running_runs(stale_before=stale_before)
    if recovered:
        await task_repo.recover_stale_tasks([run.id for run in recovered])


async def run_worker() -> None:
    settings = get_settings()
    worker_id = build_worker_id()
    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    http_client = httpx.AsyncClient()

    try:
        task_registry = create_task_registry()
        task_repo = TaskRepository(pool)
        run_repo = TaskRunRepository(pool)
        run_log_repo = TaskRunLogRepository(pool)
        log_repo = LogRepository(pool)
        crawler_client = Live12306CrawlerClient(http_client=http_client)
        settings_provider = SystemSettingsProvider(
            pool,
            ttl_seconds=SYSTEM_SETTING_CACHE_TTL_SECONDS,
        )
        geo_client = DynamicGeoClient(
            settings_provider=settings_provider,
            http_client=http_client,
        )

        runner = TaskRunner(
            pool=pool,
            task_repo=task_repo,
            run_repo=run_repo,
            run_log_repo=run_log_repo,
            log_repo=log_repo,
            crawler_client=crawler_client,
            geo_client=geo_client,
            worker_id=worker_id,
            heartbeat_interval_seconds=settings.task_worker_heartbeat_interval_seconds,
            task_registry=task_registry,
        )

        await recover_stale_runs(run_repo, task_repo)
        last_recovery = time.monotonic()

        while True:
            if time.monotonic() - last_recovery >= settings.task_worker_stale_timeout_seconds:
                await recover_stale_runs(run_repo, task_repo)
                last_recovery = time.monotonic()

            run = await run_repo.claim_next_pending_run(worker_id)
            if run is None:
                await asyncio.sleep(settings.task_worker_poll_interval_seconds)
                continue

            try:
                await runner.execute(run)
            except Exception as exc:
                await log_repo.write_log(
                    "ERROR",
                    f"worker {worker_id} 执行任务 {run.id} 失败: {exc}",
                    highlighted_terms=[run.task_type],
                )
    finally:
        await pool.close()
        await http_client.aclose()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
