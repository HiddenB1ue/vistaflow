from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_admin_auth
from app.config import get_settings
from app.schemas import APIResponse
from app.system.dependencies import CredentialServiceDep, LogServiceDep, OverviewServiceDep
from app.system.schemas import (
    CredentialResponse,
    LogResponse,
    QuotaResponse,
    SparklineResponse,
    ToggleResponse,
)

router = APIRouter(tags=["system"])


@router.get("/health")
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
    "/toggles",
    response_model=APIResponse[list[ToggleResponse]],
    dependencies=[Depends(require_admin_auth)],
)
async def list_toggles() -> APIResponse[list[ToggleResponse]]:
    toggles = [
        ToggleResponse(
            id="auto-crawl",
            label="自动爬取",
            description="启用后系统将按 cron 计划自动执行爬取任务",
            enabled=False,
        ),
        ToggleResponse(
            id="price-sync",
            label="票价同步",
            description="启用后系统将定期同步 12306 票价数据",
            enabled=False,
        ),
        ToggleResponse(
            id="geo-enrich",
            label="坐标补全",
            description="启用后新增站点将自动调用高德 API 补全经纬度",
            enabled=False,
        ),
    ]
    return APIResponse.ok(toggles)
