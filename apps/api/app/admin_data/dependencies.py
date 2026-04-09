from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.admin_data.repository import AdminDataRepository
from app.admin_data.service import AdminDataService
from app.railway.dependencies import DbPool


def get_admin_data_service(pool: DbPool) -> AdminDataService:
    return AdminDataService(repo=AdminDataRepository(pool))


AdminDataServiceDep = Annotated[AdminDataService, Depends(get_admin_data_service)]
