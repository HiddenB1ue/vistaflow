from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import asyncpg

from app.integrations.crawler.client import AbstractCrawlerClient
from app.integrations.geo.client import AbstractGeoClient
from app.models import TaskDefinition
from app.system.log_repository import LogRepository
from app.tasks.exceptions import TaskCancellationRequested
from app.tasks.progress import build_progress_snapshot
from app.tasks.repository import TaskRunLogRepository, TaskRunRepository


@dataclass(frozen=True)
class TaskFrameworkPorts:
    pool: asyncpg.Pool
    run_repo: TaskRunRepository
    run_log_repo: TaskRunLogRepository
    log_repo: LogRepository


@dataclass(frozen=True)
class TaskServiceAccess:
    crawler_client: AbstractCrawlerClient
    geo_client: AbstractGeoClient


@dataclass(frozen=True)
class TaskExecutionResult:
    summary: str
    result_level: str = "success"
    metrics_value: str = ""
    timing_value: str = ""
    progress_snapshot: dict[str, Any] | None = None
    error_message: str | None = None


@dataclass(init=False)
class TaskExecutionContext:
    task: TaskDefinition
    run_id: int
    framework: TaskFrameworkPorts
    service_access: TaskServiceAccess

    def __init__(
        self,
        *,
        task: TaskDefinition,
        run_id: int,
        framework: TaskFrameworkPorts | None = None,
        service_access: TaskServiceAccess | None = None,
        pool: asyncpg.Pool | None = None,
        run_repo: TaskRunRepository | None = None,
        run_log_repo: TaskRunLogRepository | None = None,
        log_repo: LogRepository | None = None,
        crawler_client: AbstractCrawlerClient | None = None,
        geo_client: AbstractGeoClient | None = None,
    ) -> None:
        self.task = task
        self.run_id = run_id
        self.framework = framework or TaskFrameworkPorts(
            pool=pool,
            run_repo=run_repo,
            run_log_repo=run_log_repo,
            log_repo=log_repo,
        )
        self.service_access = service_access or TaskServiceAccess(
            crawler_client=crawler_client,
            geo_client=geo_client,
        )

    @property
    def pool(self) -> asyncpg.Pool:
        return self.framework.pool

    @property
    def run_repo(self) -> TaskRunRepository:
        return self.framework.run_repo

    @property
    def run_log_repo(self) -> TaskRunLogRepository:
        return self.framework.run_log_repo

    @property
    def log_repo(self) -> LogRepository:
        return self.framework.log_repo

    @property
    def crawler_client(self) -> AbstractCrawlerClient:
        return self.service_access.crawler_client

    @property
    def geo_client(self) -> AbstractGeoClient:
        return self.service_access.geo_client

    async def log(self, severity: str, message: str) -> None:
        await self.run_log_repo.create_log(self.run_id, severity, message)
        await self.log_repo.write_log(
            severity,
            message,
            highlighted_terms=[self.task.type],
        )

    async def update_progress(self, snapshot: dict[str, Any]) -> None:
        await self.run_repo.update_progress_snapshot(self.run_id, snapshot)

    async def is_cancel_requested(self) -> bool:
        return await self.run_repo.is_cancel_requested(self.run_id)

    async def raise_if_cancel_requested(self) -> None:
        if await self.is_cancel_requested():
            raise TaskCancellationRequested(self.run_id)

    def build_progress_snapshot(
        self,
        *,
        phase: str,
        status: str,
        summary: dict[str, Any] | None = None,
        current: dict[str, Any] | None = None,
        last_error: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return build_progress_snapshot(
            self.task.type,
            phase=phase,
            status=status,
            summary=summary,
            current=current,
            last_error=last_error,
            details=details,
        )
