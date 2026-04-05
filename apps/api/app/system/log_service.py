from __future__ import annotations

from app.system.log_repository import LogRepository
from app.system.schemas import LogResponse


class LogService:
    def __init__(self, repo: LogRepository) -> None:
        self._repo = repo

    async def list_logs(self, limit: int = 100) -> list[LogResponse]:
        records = await self._repo.find_all(limit=limit)
        return [
            LogResponse(
                id=r.id,
                timestamp=r.created_at.strftime("%H:%M:%S"),
                severity=r.severity,
                message=r.message,
                highlightedTerms=r.highlighted_terms,
            )
            for r in records
        ]

    async def write_log(
        self,
        severity: str,
        message: str,
        *,
        highlighted_terms: list[str] | None = None,
    ) -> None:
        await self._repo.write_log(
            severity, message, highlighted_terms=highlighted_terms
        )
