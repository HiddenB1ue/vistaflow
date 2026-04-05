from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.railway.dependencies import DbPool
from app.system.credential_repository import CredentialRepository
from app.system.credential_service import CredentialService
from app.system.log_repository import LogRepository
from app.system.log_service import LogService
from app.system.overview_service import OverviewService


def get_credential_service(pool: DbPool) -> CredentialService:
    return CredentialService(repo=CredentialRepository(pool))


def get_log_service(pool: DbPool) -> LogService:
    return LogService(repo=LogRepository(pool))


async def get_overview_service() -> OverviewService:
    return OverviewService()


CredentialServiceDep = Annotated[CredentialService, Depends(get_credential_service)]
LogServiceDep = Annotated[LogService, Depends(get_log_service)]
OverviewServiceDep = Annotated[OverviewService, Depends(get_overview_service)]
