from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_admin_auth
from app.config import get_settings
from app.pagination import PaginatedResponse, SystemLogsQuery
from app.schemas import APIResponse
from app.system.dependencies import (
    CredentialServiceDep,
    LogServiceDep,
    OverviewServiceDep,
    SystemSettingServiceDep,
)
from app.system.schemas import (
    ActiveTaskResponse,
    CredentialResponse,
    KpiStatsResponse,
    LogResponse,
    QuotaResponse,
    SparklineResponse,
    SystemAlertResponse,
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
    response_model=APIResponse[PaginatedResponse[LogResponse]],
    dependencies=[Depends(require_admin_auth)],
)
async def list_logs(
    service: LogServiceDep,
    query: SystemLogsQuery = Depends(),
) -> APIResponse[PaginatedResponse[LogResponse]]:
    result = await service.list_logs(
        page=query.page,
        page_size=query.pageSize,
        keyword=query.keyword,
        severity=query.severity,
    )
    return APIResponse.ok(result)


@router.get(
    "/overview/sparkline",
    response_model=APIResponse[SparklineResponse],
    dependencies=[Depends(require_admin_auth)],
)
async def get_sparkline(
    service: OverviewServiceDep,
    days: int = Query(default=7, ge=1, le=30),
) -> APIResponse[SparklineResponse]:
    sparkline = await service.get_sparkline(days=days)
    return APIResponse.ok(sparkline)


@router.get(
    "/overview/quota",
    response_model=APIResponse[QuotaResponse],
    dependencies=[Depends(require_admin_auth)],
)
async def get_quota(
    service: OverviewServiceDep,
) -> APIResponse[QuotaResponse]:
    quota = await service.get_quota()
    return APIResponse.ok(quota)


@router.get(
    "/overview/kpi",
    response_model=APIResponse[KpiStatsResponse],
    dependencies=[Depends(require_admin_auth)],
)
async def get_kpi_stats(
    service: OverviewServiceDep,
) -> APIResponse[KpiStatsResponse]:
    kpi_stats = await service.get_kpi_stats()
    return APIResponse.ok(kpi_stats)


@router.get(
    "/overview/tasks",
    response_model=APIResponse[list[ActiveTaskResponse]],
    dependencies=[Depends(require_admin_auth)],
)
async def get_active_tasks(
    service: OverviewServiceDep,
) -> APIResponse[list[ActiveTaskResponse]]:
    tasks = await service.get_active_tasks()
    return APIResponse.ok(tasks)


@router.get(
    "/overview/alerts",
    response_model=APIResponse[list[SystemAlertResponse]],
    dependencies=[Depends(require_admin_auth)],
)
async def get_system_alerts(
    service: OverviewServiceDep,
) -> APIResponse[list[SystemAlertResponse]]:
    alerts = await service.get_system_alerts()
    return APIResponse.ok(alerts)


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
