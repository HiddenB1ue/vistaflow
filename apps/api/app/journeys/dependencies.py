from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.journeys.service import JourneyService
from app.railway.dependencies import DbPool
from app.railway.repository import TimetableRepository


def get_journey_service(pool: DbPool) -> JourneyService:
    return JourneyService(
        timetable_repo=TimetableRepository(pool),
    )


JourneyServiceDep = Annotated[JourneyService, Depends(get_journey_service)]
