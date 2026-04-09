from __future__ import annotations

from app.integrations.geo.client import GeoAuthError, GeoRateLimitError
from app.railway.repository import StationRepository
from app.tasks.definition import TaskCapabilityContract, TaskTypeDefinition
from app.tasks.exceptions import TaskExecutionError
from app.tasks.execution import TaskExecutionContext
from app.tasks.executor import TaskExecutorHelper
from app.tasks.payloads import FetchStationGeoPayload
from app.tasks.type_params import STATION_ADDRESS_PARAM


def _build_station_address(name: object, area_name: object) -> str:
    normalized = str(name or "").strip()
    normalized_area = str(area_name or "").strip()
    if not normalized:
        raise TaskExecutionError("站点名称为空，无法构造高德查询地址")
    station_name = normalized if normalized.endswith("站") else f"{normalized}站"
    return f"{normalized_area} {station_name}" if normalized_area else station_name


async def execute_fetch_station_geo(ctx: TaskExecutionContext):
    helper = TaskExecutorHelper(ctx)
    payload = helper.parse_payload(FetchStationGeoPayload)

    if payload.address is not None:
        await helper.begin(
            f"任务 {ctx.task.name} 开始查询地址坐标：address={payload.address}",
            total_units=1,
            current={"unitId": payload.address, "label": payload.address},
            details={
                "updatedStations": 0,
                "failedStations": 0,
                "lastResolvedAddress": None,
                "lastFailedAddress": None,
            },
        )
        await helper.checkpoint()
        coords = await ctx.geo_client.geocode_address(payload.address)
        if coords is None:
            await helper.update(
                summary={
                    "processedUnits": 1,
                    "successUnits": 0,
                    "failedUnits": 1,
                    "pendingUnits": 0,
                    "warningUnits": 1,
                },
                current={"unitId": payload.address, "label": payload.address},
                last_error={
                    "unitId": payload.address,
                    "label": payload.address,
                    "message": "未找到匹配结果",
                },
                details={
                    "updatedStations": 0,
                    "failedStations": 1,
                    "lastResolvedAddress": None,
                    "lastFailedAddress": payload.address,
                },
            )
            await ctx.log(
                "WARN",
                f"fetch-station-geo 地址查询未命中：address={payload.address}",
            )
            return helper.warning(
                summary="地址坐标查询完成，未找到匹配结果",
                metrics_value="0",
            )

        longitude, latitude = coords
        await helper.update(
            summary={
                "processedUnits": 1,
                "successUnits": 1,
                "failedUnits": 0,
                "pendingUnits": 0,
                "warningUnits": 0,
            },
            current={"unitId": payload.address, "label": payload.address},
            details={
                "updatedStations": 0,
                "failedStations": 0,
                "lastResolvedAddress": payload.address,
                "lastFailedAddress": None,
                "longitude": longitude,
                "latitude": latitude,
            },
        )
        await ctx.log(
            "SUCCESS",
            (
                "fetch-station-geo 地址查询成功："
                f"address={payload.address} longitude={longitude:.6f} latitude={latitude:.6f}"
            ),
        )
        return helper.success(summary="地址坐标查询完成", metrics_value="1")

    repo = StationRepository(ctx.pool)
    candidates = await repo.find_geo_enrichment_candidates()
    if not candidates:
        await helper.begin(
            f"任务 {ctx.task.name} 开始批量补全站点坐标",
            total_units=0,
            current={"unitId": "stations", "label": "缺失坐标站点"},
            details={
                "updatedStations": 0,
                "failedStations": 0,
                "lastResolvedAddress": None,
                "lastFailedAddress": None,
            },
        )
        await ctx.log("SUCCESS", "fetch-station-geo 无待补全站点")
        return helper.success(summary="没有待补全坐标的站点", metrics_value="0")

    await helper.begin(
        f"任务 {ctx.task.name} 开始批量补全站点坐标",
        total_units=len(candidates),
        current={"unitId": "stations", "label": "缺失坐标站点"},
        details={
            "updatedStations": 0,
            "failedStations": 0,
            "lastResolvedAddress": None,
            "lastFailedAddress": None,
        },
    )

    updated_count = 0
    failed_count = 0
    last_resolved_address: str | None = None
    last_failed_address: str | None = None

    for index, candidate in enumerate(candidates, start=1):
        await helper.checkpoint()
        station_id = int(candidate["id"])
        station_name = str(candidate["name"])
        address = _build_station_address(candidate.get("name"), candidate.get("area_name"))
        try:
            coords = await ctx.geo_client.geocode_address(address)
            if coords is None:
                failed_count += 1
                last_failed_address = address
                await helper.update(
                    summary={
                        "processedUnits": index,
                        "successUnits": updated_count,
                        "failedUnits": failed_count,
                        "pendingUnits": len(candidates) - index,
                        "warningUnits": failed_count,
                    },
                    current={"unitId": str(station_id), "label": station_name},
                    last_error={
                        "unitId": str(station_id),
                        "label": station_name,
                        "message": "未找到匹配结果",
                    },
                    details={
                        "updatedStations": updated_count,
                        "failedStations": failed_count,
                        "lastResolvedAddress": last_resolved_address,
                        "lastFailedAddress": last_failed_address,
                    },
                )
                await ctx.log(
                    "WARN",
                    (
                        "fetch-station-geo 查询失败："
                        f"station_id={station_id} station_name={station_name} address={address} error=未找到匹配结果"
                    ),
                )
                continue

            longitude, latitude = coords
            await repo.update_geo(station_id, longitude, latitude, "amap")
            updated_count += 1
            last_resolved_address = address
            await helper.update(
                summary={
                    "processedUnits": index,
                    "successUnits": updated_count,
                    "failedUnits": failed_count,
                    "pendingUnits": len(candidates) - index,
                    "warningUnits": failed_count,
                },
                current={"unitId": str(station_id), "label": station_name},
                details={
                    "updatedStations": updated_count,
                    "failedStations": failed_count,
                    "lastResolvedAddress": last_resolved_address,
                    "lastFailedAddress": last_failed_address,
                },
            )
        except GeoAuthError as exc:
            await ctx.log(
                "ERROR",
                f"fetch-station-geo 高德鉴权失败，任务中止：address={address} error={exc}",
            )
            raise TaskExecutionError(f"高德 API Key 不可用，任务已中止：{exc}") from exc
        except GeoRateLimitError as exc:
            await ctx.log(
                "ERROR",
                f"fetch-station-geo 触发高德限流，任务中止：address={address} error={exc}",
            )
            raise TaskExecutionError(f"高德接口触发限流，请稍后重试：{exc}") from exc
        except Exception as exc:
            failed_count += 1
            last_failed_address = address
            await helper.update(
                summary={
                    "processedUnits": index,
                    "successUnits": updated_count,
                    "failedUnits": failed_count,
                    "pendingUnits": len(candidates) - index,
                    "warningUnits": failed_count,
                },
                current={"unitId": str(station_id), "label": station_name},
                last_error={
                    "unitId": str(station_id),
                    "label": station_name,
                    "message": str(exc),
                },
                details={
                    "updatedStations": updated_count,
                    "failedStations": failed_count,
                    "lastResolvedAddress": last_resolved_address,
                    "lastFailedAddress": last_failed_address,
                },
            )
            await ctx.log(
                "WARN",
                (
                    "fetch-station-geo 查询失败："
                    f"station_id={station_id} station_name={station_name} address={address} error={exc}"
                ),
            )

    if updated_count == 0 and failed_count > 0:
        raise TaskExecutionError(
            f"站点坐标补全失败：success=0, failed={failed_count}, last={last_failed_address or '-'}"
        )

    if failed_count > 0:
        await ctx.log(
            "WARN",
            (
                "fetch-station-geo 完成，但存在失败站点："
                f"success={updated_count}, failed={failed_count}, last={last_failed_address or '-'}"
            ),
        )
        await ctx.log(
            "SUCCESS",
            f"fetch-station-geo 完成，成功补全 {updated_count} 个站点坐标",
        )
        return helper.warning(
            summary="站点坐标补全完成，部分站点查询失败",
            metrics_value=str(updated_count),
        )

    await ctx.log("SUCCESS", f"fetch-station-geo 完成，成功补全 {updated_count} 个站点坐标")
    return helper.success(summary="站点坐标补全完成", metrics_value=str(updated_count))


TASK_TYPE_DEFINITION = TaskTypeDefinition(
    type="fetch-station-geo",
    label="站点坐标补全",
    description="使用高德地图地址查询补全缺失站点坐标，支持单地址调试查询。",
    implemented=True,
    capability=TaskCapabilityContract(),
    param_schema=(STATION_ADDRESS_PARAM,),
    payload_model=FetchStationGeoPayload,
    executor=execute_fetch_station_geo,
)
