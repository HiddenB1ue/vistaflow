from __future__ import annotations

from app.exceptions import BusinessError
from app.journeys.schemas import (
    JourneySearchRequest,
    JourneySearchResponse,
)
from app.planner.exceptions import NoRoutesFoundError, NoTimetableDataError
from app.planner.pipeline import SearchPipeline
from app.railway.repository import TimetableRepository


class JourneyService:
    """Service for journey search operations."""

    def __init__(self, timetable_repo: TimetableRepository) -> None:
        self._pipeline = SearchPipeline(timetable_repo=timetable_repo)

    async def search(self, req: JourneySearchRequest) -> JourneySearchResponse:
        try:
            return await self._pipeline.execute(req)
        except NoTimetableDataError as e:
            raise BusinessError(
                f"暂无该日期的列车时刻数据: {e.run_date}",
                http_status=404,
            ) from e
        except NoRoutesFoundError as e:
            raise BusinessError(
                f"未找到从 {e.from_station} 到 {e.to_station} 的符合条件的路线",
                http_status=404,
            ) from e
