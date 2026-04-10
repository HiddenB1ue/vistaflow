from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.railway.dependencies import DbPool
from app.system.credential_repository import CredentialRepository
from app.system.credential_service import CredentialService
from app.system.constants import SYSTEM_SETTING_CACHE_TTL_SECONDS
from app.system.log_repository import LogRepository
from app.system.log_service import LogService
from app.system.overview_repository import OverviewRepository
from app.system.overview_service import OverviewService
from app.system.setting_repository import SystemSettingRepository
from app.system.settings_provider import SystemSettingsProvider
from app.system.settings_service import SystemSettingService


def get_credential_service(pool: DbPool) -> CredentialService:
    return CredentialService(repo=CredentialRepository(pool))


def get_log_service(pool: DbPool) -> LogService:
    return LogService(repo=LogRepository(pool))


async def get_overview_service(pool: DbPool) -> OverviewService:
    return OverviewService(repo=OverviewRepository(pool))


def get_system_settings_provider(request: Request) -> SystemSettingsProvider:
    return request.app.state.system_settings_provider  # type: ignore[no-any-return]


def build_system_settings_provider(pool: DbPool) -> SystemSettingsProvider:
    return SystemSettingsProvider(
        pool,
        ttl_seconds=SYSTEM_SETTING_CACHE_TTL_SECONDS,
    )


def get_system_setting_service(
    pool: DbPool,
    provider: Annotated[SystemSettingsProvider, Depends(get_system_settings_provider)],
) -> SystemSettingService:
    return SystemSettingService(
        repo=SystemSettingRepository(pool),
        provider=provider,
    )


CredentialServiceDep = Annotated[CredentialService, Depends(get_credential_service)]
LogServiceDep = Annotated[LogService, Depends(get_log_service)]
OverviewServiceDep = Annotated[OverviewService, Depends(get_overview_service)]
SystemSettingsProviderDep = Annotated[
    SystemSettingsProvider,
    Depends(get_system_settings_provider),
]
SystemSettingServiceDep = Annotated[
    SystemSettingService,
    Depends(get_system_setting_service),
]
