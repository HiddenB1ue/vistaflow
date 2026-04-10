from __future__ import annotations

from app.pagination import PaginatedResponse, create_paginated_response
from app.system.log_repository import LogRepository
from app.system.schemas import LogResponse


class LogService:
    def __init__(self, repo: LogRepository) -> None:
        self._repo = repo

    async def list_logs(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        keyword: str = "",
        severity: str = "all",
    ) -> PaginatedResponse[LogResponse]:
        """List system logs with pagination and filtering."""
        records, total = await self._repo.find_logs_paginated(
            page=page,
            page_size=page_size,
            keyword=keyword,
            severity=severity,
        )
        items = [
            LogResponse(
                id=r.id,
                timestamp=r.created_at.strftime("%H:%M:%S"),
                severity=r.severity,
                message=r.message,
                highlightedTerms=r.highlighted_terms,
            )
            for r in records
        ]
        return create_paginated_response(items, page, page_size, total)

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
