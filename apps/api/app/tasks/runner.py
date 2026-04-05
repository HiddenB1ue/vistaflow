from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

import asyncpg

from app.integrations.crawler.client import AbstractCrawlerClient
from app.integrations.geo.client import AbstractGeoClient
from app.models import CrawlTask
from app.system.log_repository import LogRepository
from app.tasks.handlers import (
    HandlerContext,
    handle_fetch_station,
    handle_geocode,
    handle_placeholder,
)
from app.tasks.repository import TaskRepository

# 注册表：task.type → handler 函数
# 新增任务类型只需在此处注册，runner.py 本身无需修改
Handler = Callable[[HandlerContext], Coroutine[Any, Any, None]]

TASK_HANDLERS: dict[str, Handler] = {
    "fetch-station": handle_fetch_station,
    "geocode": handle_geocode,
    "fetch-status": handle_placeholder,
    "price": handle_placeholder,
    "cleanup": handle_placeholder,
}


class TaskRunner:
    """根据任务类型从注册表分发到对应 handler 异步执行。"""

    def __init__(
        self,
        pool: asyncpg.Pool,
        task_repo: TaskRepository,
        log_repo: LogRepository,
        crawler_client: AbstractCrawlerClient,
        geo_client: AbstractGeoClient,
    ) -> None:
        self._pool = pool
        self._task_repo = task_repo
        self._log_repo = log_repo
        self._crawler_client = crawler_client
        self._geo_client = geo_client

    async def execute(self, task: CrawlTask) -> None:
        """分发执行，捕获所有异常，不向上抛出。"""
        handler = TASK_HANDLERS.get(task.type, handle_placeholder)
        ctx = HandlerContext(
            task=task,
            pool=self._pool,
            task_repo=self._task_repo,
            log_repo=self._log_repo,
            crawler_client=self._crawler_client,
            geo_client=self._geo_client,
        )
        try:
            await handler(ctx)
        except Exception as exc:
            # 最外层兜底：确保不向上抛出
            try:
                await self._task_repo.update_status(
                    task.id, "error", error_message=str(exc)
                )
                await self._log_repo.write_log(
                    "ERROR",
                    f"任务 {task.name} 执行异常: {exc}",
                    highlighted_terms=[task.type],
                )
            except Exception:
                pass  # 日志写入也失败时静默
