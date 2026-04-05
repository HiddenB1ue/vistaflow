from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.integrations.ticket_12306.client import AbstractTicketClient
from app.railway.dependencies import DbPool
from app.railway.repository import StationRepository, TimetableRepository

from app.journeys.service import JourneyService


def get_ticket_client(request: Request) -> AbstractTicketClient:
    return request.app.state.ticket_client  # type: ignore[no-any-return]


def get_journey_service(
    pool: DbPool,
    ticket_client: AbstractTicketClient = Depends(get_ticket_client),
) -> JourneyService:
    return JourneyService(
        timetable_repo=TimetableRepository(pool),
        station_repo=StationRepository(pool),
        ticket_client=ticket_client,
    )


JourneyServiceDep = Annotated[JourneyService, Depends(get_journey_service)]
