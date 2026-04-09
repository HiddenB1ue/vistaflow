from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_admin_auth
from app.config import get_settings
from app.schemas import APIResponse
from app.system.dependencies import (
    CredentialServiceDep,
    LogServiceDep,
    OverviewServiceDep,
    SystemSettingServiceDep,
)
from app.system.schemas import (
    CredentialResponse,
    LogResponse,
    QuotaResponse,
    SparklineResponse,
    SystemSettingBatchUpdateRequest,
    SystemSettingBatchUpdateResponse,
    SystemSettingResponse,
    ToggleResponse,
)

health_router = APIRouter(tags=["system"])
router = APIRouter(prefix="/system", tags=["system"])


@health_router.get("/healthz")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "env": settings.app_env,
        "version": settings.app_version,
        "time": datetime.now(UTC).isoformat(),
    }


# --- 需鉴权路由 ---


@router.get(
    "/credentials",
    response_model=APIResponse[list[CredentialResponse]],
    dependencies=[Depends(require_admin_auth)],
)
async def list_credentials(
    service: CredentialServiceDep,
) -> APIResponse[list[CredentialResponse]]:
    credentials = await service.list_credentials()
    return APIResponse.ok(credentials)


@router.get(
    "/logs",
    response_model=APIResponse[list[LogResponse]],
    dependencies=[Depends(require_admin_auth)],
)
async def list_logs(
    service: LogServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> APIResponse[list[LogResponse]]:
    logs = await service.list_logs(limit=limit)
    return APIResponse.ok(logs)


@router.get(
    "/overview/sparkline",
    response_model=APIResponse[SparklineResponse],
    dependencies=[Depends(require_admin_auth)],
)
async def get_sparkline(
    service: OverviewServiceDep,
) -> APIResponse[SparklineResponse]:
    return APIResponse.ok(service.get_sparkline())


@router.get(
    "/overview/quota",
    response_model=APIResponse[QuotaResponse],
    dependencies=[Depends(require_admin_auth)],
)
async def get_quota(
    service: OverviewServiceDep,
) -> APIResponse[QuotaResponse]:
    return APIResponse.ok(service.get_quota())


@router.get(
    "/settings",
    response_model=APIResponse[list[SystemSettingResponse]],
    dependencies=[Depends(require_admin_auth)],
)
async def list_settings(
    service: SystemSettingServiceDep,
) -> APIResponse[list[SystemSettingResponse]]:
    settings = await service.list_settings()
    return APIResponse.ok(settings)


@router.patch(
    "/settings",
    response_model=APIResponse[SystemSettingBatchUpdateResponse],
    dependencies=[Depends(require_admin_auth)],
)
async def update_settings(
    payload: SystemSettingBatchUpdateRequest,
    service: SystemSettingServiceDep,
) -> APIResponse[SystemSettingBatchUpdateResponse]:
    result = await service.update_settings(payload)
    return APIResponse.ok(result)


@router.get(
    "/toggles",
    response_model=APIResponse[list[ToggleResponse]],
    dependencies=[Depends(require_admin_auth)],
)
async def list_toggles(
    service: SystemSettingServiceDep,
) -> APIResponse[list[ToggleResponse]]:
    toggles = await service.list_toggles()
    return APIResponse.ok(toggles)
