from __future__ import annotations

from copy import deepcopy
from typing import Any


def stage_for_status(status: str) -> str:
    if status == "pending":
        return "pending"
    if status == "running":
        return "crawling"
    return status


def build_progress_snapshot(
    task_type: str,
    *,
    stage: str,
    status: str,
    summary: dict[str, int] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_summary = {
        "processedUnits": 0,
        "pendingUnits": 0,
        "successUnits": 0,
        "failedUnits": 0,
    }
    if summary is not None:
        base_summary.update(
            {
                key: int(value)
                for key, value in summary.items()
                if key in base_summary
            }
        )
    return {
        "version": 1,
        "taskType": task_type,
        "stage": stage,
        "status": status,
        "summary": base_summary,
        "details": deepcopy(details) if details is not None else {},
    }


def ensure_progress_snapshot(
    snapshot: Any,
    *,
    task_type: str,
    stage: str,
    status: str,
) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return build_progress_snapshot(task_type, stage=stage, status=status)

    summary = snapshot.get("summary")
    details = snapshot.get("details")
    return build_progress_snapshot(
        str(snapshot.get("taskType") or task_type),
        stage=str(snapshot.get("stage") or stage),
        status=str(snapshot.get("status") or status),
        summary=summary if isinstance(summary, dict) else None,
        details=details if isinstance(details, dict) else None,
    )


def with_progress_state(
    snapshot: Any,
    *,
    task_type: str,
    stage: str,
    status: str,
) -> dict[str, Any]:
    base = ensure_progress_snapshot(
        snapshot,
        task_type=task_type,
        stage=stage,
        status=status,
    )
    base["taskType"] = task_type
    base["stage"] = stage
    base["status"] = status
    return base
