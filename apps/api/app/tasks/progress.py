from __future__ import annotations

from copy import deepcopy
from typing import Any


_SUMMARY_KEYS = (
    "totalUnits",
    "processedUnits",
    "successUnits",
    "failedUnits",
    "pendingUnits",
    "warningUnits",
)


def phase_for_status(status: str) -> str:
    if status == "pending":
        return "queued"
    if status == "running":
        return "processing"
    return status


def _normalize_summary(summary: dict[str, Any] | None) -> dict[str, int]:
    normalized = {key: 0 for key in _SUMMARY_KEYS}
    if summary is None:
        return normalized
    for key in _SUMMARY_KEYS:
        if key in summary:
            normalized[key] = int(summary[key])
    return normalized


def build_progress_snapshot(
    task_type: str,
    *,
    phase: str,
    status: str,
    summary: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
    last_error: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "version": 2,
        "taskType": task_type,
        "phase": phase,
        "status": status,
        "summary": _normalize_summary(summary),
        "current": deepcopy(current) if current is not None else {},
        "lastError": deepcopy(last_error) if last_error is not None else {},
        "details": deepcopy(details) if details is not None else {},
    }


def ensure_progress_snapshot(
    snapshot: Any,
    *,
    task_type: str,
    phase: str,
    status: str,
) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return build_progress_snapshot(task_type, phase=phase, status=status)

    snapshot_phase = str(snapshot.get("phase") or snapshot.get("stage") or phase)
    summary = snapshot.get("summary")
    current = snapshot.get("current")
    last_error = snapshot.get("lastError")
    details = snapshot.get("details")

    return build_progress_snapshot(
        str(snapshot.get("taskType") or task_type),
        phase=snapshot_phase,
        status=str(snapshot.get("status") or status),
        summary=summary if isinstance(summary, dict) else None,
        current=current if isinstance(current, dict) else None,
        last_error=last_error if isinstance(last_error, dict) else None,
        details=details if isinstance(details, dict) else None,
    )


def with_progress_state(
    snapshot: Any,
    *,
    task_type: str,
    phase: str,
    status: str,
) -> dict[str, Any]:
    base = ensure_progress_snapshot(snapshot, task_type=task_type, phase=phase, status=status)
    base["taskType"] = task_type
    base["phase"] = phase
    base["status"] = status
    return base
