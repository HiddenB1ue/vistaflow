from __future__ import annotations

from typing import Annotated, cast

import asyncpg
from fastapi import Depends, Request

from app.integrations.ticket_12306.client import (
    AbstractTicketClient,
)
from app.repositories.station_repository import StationRepository
from app.repositories.timetable_repository import TimetableRepository
from app.repositories.train_repository import TrainRepository
from app.services.journey_service import JourneyService
from app.services.station_service import StationService
from app.services.train_service import TrainService


def get_db_pool(request: Request) -> asyncpg.Pool:
    return cast(asyncpg.Pool, request.app.state.db_pool)


def get_ticket_client(request: Request) -> AbstractTicketClient:
    return cast(AbstractTicketClient, request.app.state.ticket_client)


DbPool = Annotated[asyncpg.Pool, Depends(get_db_pool)]
TicketClientDep = Annotated[AbstractTicketClient, Depends(get_ticket_client)]


def get_journey_service(
    pool: DbPool,
    ticket_client: TicketClientDep,
) -> JourneyService:
    return JourneyService(
        timetable_repo=TimetableRepository(pool),
        station_repo=StationRepository(pool),
        ticket_client=ticket_client,
    )


def get_train_service(pool: DbPool) -> TrainService:
    return TrainService(repo=TrainRepository(pool))


def get_station_service(pool: DbPool) -> StationService:
    return StationService(repo=StationRepository(pool))


JourneyServiceDep = Annotated[JourneyService, Depends(get_journey_service)]
TrainServiceDep = Annotated[TrainService, Depends(get_train_service)]
StationServiceDep = Annotated[StationService, Depends(get_station_service)]
