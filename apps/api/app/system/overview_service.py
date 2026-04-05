from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.system.schemas import QuotaResponse, SparklineResponse


class OverviewService:
    def get_sparkline(self) -> SparklineResponse:
        today = datetime.now(UTC).date()
        labels = [
            (today - timedelta(days=6 - i)).isoformat() for i in range(7)
        ]
        return SparklineResponse(values=[0] * 7, labels=labels)

    def get_quota(self) -> QuotaResponse:
        return QuotaResponse(percentage=0, used=0, total=0)
