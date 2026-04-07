from __future__ import annotations

from typing import Any

from app.database import BaseRepository
from app.models import TaskDefinition, TaskRun, TaskRunLog
from app.tasks.progress import stage_for_status, with_progress_state

DEFAULT_METRICS_LABEL = "最近结果"
DEFAULT_TIMING_LABEL = "最近耗时"
RECOVERY_MESSAGE = "应用重启前任务未正常结束"


class TaskRepository(BaseRepository):
    async def find_all(self) -> list[TaskDefinition]:
        sql = """
            SELECT id, name, type, type_label, description, enabled, cron, payload,
                   status, latest_run_id, latest_run_status, latest_run_started_at,
                   latest_run_finished_at, latest_error_message, metrics_label,
                   metrics_value, timing_label, timing_value, error_message,
                   created_at, updated_at
            FROM task
            ORDER BY updated_at DESC, id DESC
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [self._row_to_task(row) for row in rows]

    async def find_by_id(self, task_id: int) -> TaskDefinition | None:
        sql = """
            SELECT id, name, type, type_label, description, enabled, cron, payload,
                   status, latest_run_id, latest_run_status, latest_run_started_at,
                   latest_run_finished_at, latest_error_message, metrics_label,
                   metrics_value, timing_label, timing_value, error_message,
                   created_at, updated_at
            FROM task
            WHERE id = $1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, task_id)
        return self._row_to_task(row) if row is not None else None

    async def find_by_name(self, name: str) -> TaskDefinition | None:
        sql = """
            SELECT id, name, type, type_label, description, enabled, cron, payload,
                   status, latest_run_id, latest_run_status, latest_run_started_at,
                   latest_run_finished_at, latest_error_message, metrics_label,
                   metrics_value, timing_label, timing_value, error_message,
                   created_at, updated_at
            FROM task
            WHERE name = $1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, name)
        return self._row_to_task(row) if row is not None else None

    async def create_task(
        self,
        *,
        name: str,
        task_type: str,
        type_label: str,
        description: str | None,
        enabled: bool,
        cron: str | None,
        payload: dict[str, Any],
    ) -> TaskDefinition:
        sql = """
            INSERT INTO task (
                name, type, type_label, description, enabled, cron, payload,
                status, metrics_label, metrics_value, timing_label, timing_value
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'idle', $8, '', $9, '')
            RETURNING id, name, type, type_label, description, enabled, cron, payload,
                      status, latest_run_id, latest_run_status, latest_run_started_at,
                      latest_run_finished_at, latest_error_message, metrics_label,
                      metrics_value, timing_label, timing_value, error_message,
                      created_at, updated_at
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                sql,
                name,
                task_type,
                type_label,
                description,
                enabled,
                cron,
                payload,
                DEFAULT_METRICS_LABEL,
                DEFAULT_TIMING_LABEL,
            )
        if row is None:
            raise RuntimeError("Failed to create task")
        return self._row_to_task(row)

    async def update_task(
        self,
        task_id: int,
        *,
        name: str,
        task_type: str,
        type_label: str,
        description: str | None,
        enabled: bool,
        cron: str | None,
        payload: dict[str, Any],
    ) -> TaskDefinition:
        sql = """
            UPDATE task
            SET name = $2,
                type = $3,
                type_label = $4,
                description = $5,
                enabled = $6,
                cron = $7,
                payload = $8,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id, name, type, type_label, description, enabled, cron, payload,
                      status, latest_run_id, latest_run_status, latest_run_started_at,
                      latest_run_finished_at, latest_error_message, metrics_label,
                      metrics_value, timing_label, timing_value, error_message,
                      created_at, updated_at
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                sql,
                task_id,
                name,
                task_type,
                type_label,
                description,
                enabled,
                cron,
                payload,
            )
        if row is None:
            raise RuntimeError(f"Failed to update task {task_id}")
        return self._row_to_task(row)

    async def delete_task(self, task_id: int) -> None:
        sql = "DELETE FROM task WHERE id = $1"
        async with self._pool.acquire() as conn:
            await conn.execute(sql, task_id)

    async def mark_task_running(self, task_id: int, run_id: int) -> None:
        sql = """
            UPDATE task
            SET status = 'running',
                latest_run_id = $2,
                latest_run_status = 'running',
                latest_run_started_at = NOW(),
                latest_run_finished_at = NULL,
                latest_error_message = NULL,
                error_message = NULL,
                updated_at = NOW()
            WHERE id = $1
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, task_id, run_id)

    async def apply_run_result(
        self,
        task_id: int,
        run_id: int,
        status: str,
        *,
        error_message: str | None = None,
        metrics_value: str | None = None,
        timing_value: str | None = None,
    ) -> None:
        sql = """
            UPDATE task
            SET status = $2,
                latest_run_id = $3,
                latest_run_status = $2,
                latest_run_finished_at = NOW(),
                latest_error_message = $4,
                error_message = $4,
                metrics_value = COALESCE($5, metrics_value),
                timing_value = COALESCE($6, timing_value),
                updated_at = NOW()
            WHERE id = $1
        """
        async with self._pool.acquire() as conn:
            await conn.execute(
                sql,
                task_id,
                status,
                run_id,
                error_message,
                metrics_value,
                timing_value,
            )

    async def recover_incomplete_tasks(self) -> None:
        sql = """
            UPDATE task
            SET status = 'terminated',
                latest_run_status = 'terminated',
                latest_run_finished_at = NOW(),
                latest_error_message = $1,
                error_message = $1,
                updated_at = NOW()
            WHERE status = 'running' OR latest_run_status IN ('pending', 'running')
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, RECOVERY_MESSAGE)

    @staticmethod
    def _row_to_task(row: Any) -> TaskDefinition:
        record = dict(row)
        return TaskDefinition(
            id=int(record["id"]),
            name=str(record["name"]),
            type=str(record["type"]),
            type_label=str(record["type_label"]),
            description=record.get("description"),
            enabled=bool(record.get("enabled", True)),
            cron=record.get("cron"),
            payload=dict(record.get("payload") or {}),
            status=str(record["status"]),
            latest_run_id=(
                int(record["latest_run_id"])
                if record.get("latest_run_id") is not None
                else None
            ),
            latest_run_status=(
                str(record["latest_run_status"])
                if record.get("latest_run_status") is not None
                else None
            ),
            latest_run_started_at=record.get("latest_run_started_at"),
            latest_run_finished_at=record.get("latest_run_finished_at"),
            latest_error_message=record.get("latest_error_message"),
            metrics_label=str(record.get("metrics_label") or DEFAULT_METRICS_LABEL),
            metrics_value=str(record.get("metrics_value") or ""),
            timing_label=str(record.get("timing_label") or DEFAULT_TIMING_LABEL),
            timing_value=str(record.get("timing_value") or ""),
            error_message=record.get("error_message"),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )


class TaskRunRepository(BaseRepository):
    async def create_run(
        self,
        *,
        task_id: int,
        requested_by: str = "admin",
    ) -> TaskRun:
        sql = """
            INSERT INTO task_run (
                task_id, task_name, task_type, trigger_mode, status, requested_by, progress_snapshot
            )
            SELECT id, name, type, 'manual', 'pending', $2, NULL
            FROM task
            WHERE id = $1
            RETURNING id, task_id, task_name, task_type, trigger_mode, status,
                      requested_by, summary, metrics_value, progress_snapshot, error_message,
                      termination_reason, started_at, finished_at, created_at,
                      updated_at
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, task_id, requested_by)
        if row is None:
            raise RuntimeError(f"Failed to create run for task {task_id}")
        return self._row_to_run(row)

    async def find_by_id(self, run_id: int) -> TaskRun | None:
        sql = """
            SELECT id, task_id, task_name, task_type, trigger_mode, status,
                   requested_by, summary, metrics_value, progress_snapshot, error_message,
                   termination_reason, started_at, finished_at, created_at,
                   updated_at
            FROM task_run
            WHERE id = $1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, run_id)
        return self._row_to_run(row) if row is not None else None

    async def find_active_by_task(self, task_id: int) -> TaskRun | None:
        sql = """
            SELECT id, task_id, task_name, task_type, trigger_mode, status,
                   requested_by, summary, metrics_value, progress_snapshot, error_message,
                   termination_reason, started_at, finished_at, created_at,
                   updated_at
            FROM task_run
            WHERE task_id = $1
              AND status IN ('pending', 'running')
            ORDER BY created_at DESC
            LIMIT 1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, task_id)
        return self._row_to_run(row) if row is not None else None

    async def list_by_task(self, task_id: int) -> list[TaskRun]:
        sql = """
            SELECT id, task_id, task_name, task_type, trigger_mode, status,
                   requested_by, summary, metrics_value, progress_snapshot, error_message,
                   termination_reason, started_at, finished_at, created_at,
                   updated_at
            FROM task_run
            WHERE task_id = $1
            ORDER BY created_at DESC, id DESC
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, task_id)
        return [self._row_to_run(row) for row in rows]

    async def update_run_status(
        self,
        run_id: int,
        status: str,
        *,
        summary: str | None = None,
        metrics_value: str | None = None,
        progress_snapshot: dict[str, Any] | None = None,
        error_message: str | None = None,
        termination_reason: str | None = None,
        set_started: bool = False,
        set_finished: bool = False,
    ) -> TaskRun:
        sql = """
            UPDATE task_run
            SET status = $2,
                summary = COALESCE($3, summary),
                metrics_value = COALESCE($4, metrics_value),
                progress_snapshot = COALESCE($5, progress_snapshot),
                error_message = $6,
                termination_reason = $7,
                started_at = CASE
                    WHEN $8 THEN COALESCE(started_at, NOW())
                    ELSE started_at
                END,
                finished_at = CASE
                    WHEN $9 THEN NOW()
                    ELSE finished_at
                END,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id, task_id, task_name, task_type, trigger_mode, status,
                      requested_by, summary, metrics_value, progress_snapshot, error_message,
                      termination_reason, started_at, finished_at, created_at,
                      updated_at
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                sql,
                run_id,
                status,
                summary,
                metrics_value,
                progress_snapshot,
                error_message,
                termination_reason,
                set_started,
                set_finished,
            )
        if row is None:
            raise RuntimeError(f"Failed to update run {run_id}")
        return self._row_to_run(row)

    async def update_progress_snapshot(
        self,
        run_id: int,
        progress_snapshot: dict[str, Any],
    ) -> TaskRun:
        sql = """
            UPDATE task_run
            SET progress_snapshot = $2,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id, task_id, task_name, task_type, trigger_mode, status,
                      requested_by, summary, metrics_value, progress_snapshot, error_message,
                      termination_reason, started_at, finished_at, created_at,
                      updated_at
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, run_id, progress_snapshot)
        if row is None:
            raise RuntimeError(f"Failed to update progress snapshot for run {run_id}")
        return self._row_to_run(row)

    async def recover_incomplete_runs(self) -> None:
        sql = """
            UPDATE task_run
            SET status = 'terminated',
                progress_snapshot = CASE
                    WHEN progress_snapshot IS NULL THEN NULL
                    ELSE jsonb_set(
                        jsonb_set(progress_snapshot, '{stage}', '\"terminated\"'::jsonb, true),
                        '{status}',
                        '\"terminated\"'::jsonb,
                        true
                    )
                END,
                termination_reason = $1,
                error_message = COALESCE(error_message, $1),
                finished_at = COALESCE(finished_at, NOW()),
                updated_at = NOW()
            WHERE status IN ('pending', 'running')
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, RECOVERY_MESSAGE)

    @staticmethod
    def _row_to_run(row: Any) -> TaskRun:
        record = dict(row)
        return TaskRun(
            id=int(record["id"]),
            task_id=int(record["task_id"]),
            task_name=str(record["task_name"]),
            task_type=str(record["task_type"]),
            trigger_mode=str(record["trigger_mode"]),
            status=str(record["status"]),
            requested_by=str(record.get("requested_by") or "admin"),
            summary=record.get("summary"),
            metrics_value=str(record.get("metrics_value") or ""),
            progress_snapshot=(
                with_progress_state(
                    record.get("progress_snapshot"),
                    task_type=str(record["task_type"]),
                    stage=stage_for_status(str(record.get("status") or "pending")),
                    status=str(record.get("status") or "pending"),
                )
                if record.get("progress_snapshot") is not None
                else None
            ),
            error_message=record.get("error_message"),
            termination_reason=record.get("termination_reason"),
            started_at=record.get("started_at"),
            finished_at=record.get("finished_at"),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )


class TaskRunLogRepository(BaseRepository):
    async def create_log(self, run_id: int, severity: str, message: str) -> TaskRunLog:
        sql = """
            INSERT INTO task_run_log (run_id, severity, message)
            VALUES ($1, $2, $3)
            RETURNING id, run_id, severity, message, created_at
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, run_id, severity, message)
        if row is None:
            raise RuntimeError(f"Failed to create run log for run {run_id}")
        return self._row_to_log(row)

    async def list_by_run(self, run_id: int) -> list[TaskRunLog]:
        sql = """
            SELECT id, run_id, severity, message, created_at
            FROM task_run_log
            WHERE run_id = $1
            ORDER BY created_at ASC, id ASC
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, run_id)
        return [self._row_to_log(row) for row in rows]

    @staticmethod
    def _row_to_log(row: Any) -> TaskRunLog:
        record = dict(row)
        return TaskRunLog(
            id=int(record["id"]),
            run_id=int(record["run_id"]),
            severity=str(record["severity"]),
            message=str(record["message"]),
            created_at=record["created_at"],
        )
