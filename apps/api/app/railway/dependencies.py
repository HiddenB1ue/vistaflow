from __future__ import annotations

from typing import Annotated, cast

import asyncpg
from fastapi import Depends, Request

from app.railway.repository import StationRepository, TrainRepository
from app.railway.service import StationService, TrainService


def get_db_pool(request: Request) -> asyncpg.Pool:
    return cast(asyncpg.Pool, request.app.state.db_pool)


DbPool = Annotated[asyncpg.Pool, Depends(get_db_pool)]


def get_train_service(pool: DbPool) -> TrainService:
    return TrainService(repo=TrainRepository(pool))


def get_station_service(pool: DbPool) -> StationService:
    return StationService(repo=StationRepository(pool))


TrainServiceDep = Annotated[TrainService, Depends(get_train_service)]
StationServiceDep = Annotated[StationService, Depends(get_station_service)]
