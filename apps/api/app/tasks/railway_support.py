from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.railway.repository import RailwayTaskRepository
from app.tasks.progress import build_progress_snapshot


@dataclass
class FetchTrainsProgressStats:
    total_seed_keywords: int = 0
    current_seed_keyword: str | None = None
    completed_seed_keywords: int = 0
    failed_seed_keywords: int = 0
    last_completed_seed_keyword: str | None = None
    last_failed_seed_keyword: str | None = None
    raw_rows_fetched: int = 0
    unique_train_nos_seen: int = 0
    trains_upsert_attempted: int = 0
    duplicate_rows_skipped: int = 0

    def to_snapshot(
        self,
        *,
        phase: str = "processing",
        status: str = "running",
    ) -> dict[str, Any]:
        processed_units = self.completed_seed_keywords + self.failed_seed_keywords
        pending_units = max(0, self.total_seed_keywords - processed_units)
        return build_progress_snapshot(
            "fetch-trains",
            phase=phase,
            status=status,
            summary={
                "totalUnits": self.total_seed_keywords,
                "processedUnits": processed_units,
                "pendingUnits": pending_units,
                "successUnits": self.completed_seed_keywords,
                "failedUnits": self.failed_seed_keywords,
                "warningUnits": self.failed_seed_keywords,
            },
            current={
                "unitId": self.current_seed_keyword,
                "label": self.current_seed_keyword,
            },
            last_error=(
                {
                    "unitId": self.last_failed_seed_keyword,
                    "label": self.last_failed_seed_keyword,
                    "message": "seed failed",
                }
                if self.last_failed_seed_keyword
                else None
            ),
            details={
                "pendingSeedKeywords": pending_units,
                "completedSeedKeywords": self.completed_seed_keywords,
                "failedSeedKeywords": self.failed_seed_keywords,
                "lastCompletedSeedKeyword": self.last_completed_seed_keyword,
                "lastFailedSeedKeyword": self.last_failed_seed_keyword,
                "rawRowsFetched": self.raw_rows_fetched,
                "uniqueTrainNosSeen": self.unique_train_nos_seen,
                "trainsUpsertAttempted": self.trains_upsert_attempted,
                "duplicateRowsSkipped": self.duplicate_rows_skipped,
            },
        )


async def resolve_stop_target_train_nos(
    repo: RailwayTaskRepository,
    keyword: str | None,
) -> list[str]:
    if keyword is None or not keyword.strip():
        return await repo.list_all_train_nos()
    return await repo.find_train_nos_by_keyword(keyword)


def derive_train_rows_from_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dedup: dict[str, dict[str, Any]] = {}
    for row in rows:
        train_no = str(row.get("train_no") or "").strip()
        if not train_no:
            continue
        dedup[train_no] = {
            "train_no": train_no,
            "station_train_code": row.get("station_train_code"),
            "from_station": row.get("from_station"),
            "to_station": row.get("to_station"),
            "total_num": row.get("total_num"),
        }
    return list(dedup.values())


def build_train_run_rows(
    raw_rows: list[dict[str, Any]],
    *,
    run_date: str,
    keyword: str,
) -> list[dict[str, Any]]:
    normalized_run_date = run_date.strip()
    normalized_keyword = keyword.strip().upper()
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        station_train_code = str(row.get("station_train_code") or "").strip().upper()
        if not station_train_code or not station_train_code.startswith(normalized_keyword):
            continue

        row_run_date = str(row.get("run_date") or "").strip()
        row_compact_date = str(row.get("date") or "").strip()
        if row_run_date:
            normalized_row_run_date = row_run_date
        elif len(row_compact_date) == 8 and row_compact_date.isdigit():
            normalized_row_run_date = (
                f"{row_compact_date[:4]}-{row_compact_date[4:6]}-{row_compact_date[6:8]}"
            )
        else:
            normalized_row_run_date = ""

        if normalized_row_run_date != normalized_run_date:
            continue

        rows.append(
            {
                "train_no": row.get("train_no"),
                "station_train_code": row.get("station_train_code"),
                "from_station": row.get("from_station"),
                "to_station": row.get("to_station"),
                "total_num": row.get("total_num"),
                "run_date": normalized_run_date,
                "status": run_status_from_flag(row.get("data_flag")),
            }
        )
    return rows


def run_status_from_flag(value: Any) -> str:
    text = str(value if value is not None else "").strip().lower()
    if text in {"", "none", "null", "1", "true", "t", "yes", "y", "on"}:
        return "running"
    if text in {"0", "false", "f", "no", "n", "off"}:
        return "suspended"
    if "suspend" in text or "cancel" in text:
        return "suspended"
    return "unknown"
