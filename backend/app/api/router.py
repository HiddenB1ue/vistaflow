from __future__ import annotations

from fastapi import APIRouter

from app.api import health, journeys, stations, trains

router = APIRouter()

router.include_router(health.router)
router.include_router(journeys.router, prefix="/api")
router.include_router(trains.router, prefix="/api")
router.include_router(stations.router, prefix="/api")
