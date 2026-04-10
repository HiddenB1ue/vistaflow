from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.system.overview_repository import OverviewRepository
from app.system.schemas import (
    ActiveTaskResponse,
    KpiStatsResponse,
    QuotaResponse,
    SparklineResponse,
    SystemAlertResponse,
)


class OverviewService:
    def __init__(self, repo: OverviewRepository) -> None:
        self._repo = repo

    async def get_kpi_stats(self) -> KpiStatsResponse:
        """Aggregate all KPI statistics."""
        total_records = await self._repo.count_total_records()
        stations_with_coords, total_stations = await self._repo.count_stations_with_coordinates()
        coord_completion_rate = (
            (stations_with_coords / total_stations * 100) if total_stations > 0 else 0.0
        )
        
        # Get pending alerts count (WARN and ERROR severity)
        alerts = await self._repo.get_recent_alerts(limit=100)
        pending_alerts = sum(1 for alert in alerts if alert.severity in ("WARN", "ERROR"))
        
        today_api_calls = await self._repo.count_todays_api_calls()
        
        # Placeholder for remaining quota - in real implementation, this would query actual API usage
        remaining_quota = 100_000 - today_api_calls

        return KpiStatsResponse(
            totalRecords=total_records,
            stationCoverage=total_stations,
            coordCompletionRate=round(coord_completion_rate, 1),
            pendingAlerts=pending_alerts,
            todayApiCalls=today_api_calls,
            remainingQuota=max(0, remaining_quota),
        )

    async def get_sparkline(self, days: int = 7) -> SparklineResponse:
        """Get daily record counts for trend chart."""
        daily_counts = await self._repo.count_daily_records(days)
        values = [dc.count for dc in daily_counts]
        labels = [dc.date.isoformat() for dc in daily_counts]
        return SparklineResponse(values=values, labels=labels)

    async def get_quota(self) -> QuotaResponse:
        """Get API quota information."""
        # Placeholder logic - in real implementation, this would query actual API usage tracking
        today_api_calls = await self._repo.count_todays_api_calls()
        total_quota = 100_000
        used = min(today_api_calls, total_quota)
        percentage = int((used / total_quota * 100)) if total_quota > 0 else 0
        
        return QuotaResponse(
            percentage=percentage,
            used=used,
            total=total_quota,
        )

    async def get_active_tasks(self) -> list[ActiveTaskResponse]:
        """Get currently running or pending tasks with elapsed time."""
        tasks = await self._repo.get_active_tasks(limit=5)
        now = datetime.now(UTC)
        
        result = []
        for task in tasks:
            elapsed_time = None
            started_at = None
            
            if task.started_at:
                started_at = task.started_at.isoformat()
                if task.status == "running":
                    # Calculate elapsed time
                    delta = now - task.started_at
                    hours, remainder = divmod(int(delta.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    elapsed_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            result.append(
                ActiveTaskResponse(
                    id=task.id,
                    name=task.name,
                    status=task.status,
                    elapsedTime=elapsed_time,
                    startedAt=started_at,
                )
            )
        
        return result

    async def get_system_alerts(self) -> list[SystemAlertResponse]:
        """Get recent system alerts with severity mapping."""
        alerts = await self._repo.get_recent_alerts(limit=3)
        
        # Map severity to frontend-friendly values
        severity_map = {
            "SUCCESS": "success",
            "INFO": "info",
            "WARN": "warning",
            "ERROR": "warning",
            "SYSTEM": "info",
        }
        
        result = []
        for alert in alerts:
            severity = severity_map.get(alert.severity, "info")
            
            # Generate a title based on severity
            title_map = {
                "success": "操作成功",
                "info": "系统信息",
                "warning": "系统警告",
            }
            title = title_map.get(severity, "系统通知")
            
            result.append(
                SystemAlertResponse(
                    id=alert.id,
                    severity=severity,
                    title=title,
                    message=alert.message,
                    timestamp=alert.created_at.isoformat(),
                )
            )
        
        return result
