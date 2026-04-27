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
from app.tasks.scheduler import TaskScheduler


def build_worker_id() -> str:
    return f"{socket.gethostname()}-{os.getpid()}"


def normalize_worker_concurrency(value: int) -> int:
    return max(1, value)


def build_worker_slot_id(worker_id: str, slot_index: int) -> str:
    return f"{worker_id}-slot-{slot_index + 1}"


async def recover_stale_runs(run_repo: TaskRunRepository, task_repo: TaskRepository) -> None:
    settings = get_settings()
    stale_before = datetime.now(UTC) - timedelta(
        seconds=settings.task_worker_stale_timeout_seconds
    )
    recovered = await run_repo.recover_stale_running_runs(stale_before=stale_before)
    if recovered:
        await task_repo.recover_stale_tasks([run.id for run in recovered])


async def run_scheduler_loop(
    *,
    scheduler: TaskScheduler,
    run_repo: TaskRunRepository,
    task_repo: TaskRepository,
    log_repo: LogRepository,
    stale_timeout_seconds: float,
    poll_interval_seconds: float,
) -> None:
    await recover_stale_runs(run_repo, task_repo)
    last_recovery = time.monotonic()

    while True:
        if time.monotonic() - last_recovery >= stale_timeout_seconds:
            await recover_stale_runs(run_repo, task_repo)
            last_recovery = time.monotonic()

        try:
            await scheduler.enqueue_due_tasks()
        except Exception as exc:
            await log_repo.write_log(
                "ERROR",
                f"任务调度器入队失败: {exc}",
                highlighted_terms=["scheduler"],
            )
        await asyncio.sleep(poll_interval_seconds)


async def run_consumer_loop(
    *,
    worker_id: str,
    run_repo: TaskRunRepository,
    runner: TaskRunner,
    log_repo: LogRepository,
    poll_interval_seconds: float,
    stop_after_runs: int | None = None,
) -> None:
    executed_runs = 0
    while True:
        run = await run_repo.claim_next_pending_run(worker_id)
        if run is None:
            await asyncio.sleep(poll_interval_seconds)
            continue

        try:
            await runner.execute(run)
        except Exception as exc:
            await log_repo.write_log(
                "ERROR",
                f"worker {worker_id} 执行任务 {run.id} 失败: {exc}",
                highlighted_terms=[run.task_type],
            )
        executed_runs += 1
        if stop_after_runs is not None and executed_runs >= stop_after_runs:
            return


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
        scheduler = TaskScheduler(task_repo)
        concurrency = normalize_worker_concurrency(settings.task_worker_concurrency)
        scheduler_task = asyncio.create_task(
            run_scheduler_loop(
                scheduler=scheduler,
                run_repo=run_repo,
                task_repo=task_repo,
                log_repo=log_repo,
                stale_timeout_seconds=settings.task_worker_stale_timeout_seconds,
                poll_interval_seconds=settings.task_worker_poll_interval_seconds,
            )
        )
        consumer_tasks = [
            asyncio.create_task(
                run_consumer_loop(
                    worker_id=build_worker_slot_id(worker_id, slot_index),
                    run_repo=run_repo,
                    runner=runner,
                    log_repo=log_repo,
                    poll_interval_seconds=settings.task_worker_poll_interval_seconds,
                )
            )
            for slot_index in range(concurrency)
        ]
        await asyncio.gather(scheduler_task, *consumer_tasks)
    finally:
        await pool.close()
        await http_client.aclose()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
