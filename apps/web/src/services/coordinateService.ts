/**
 * Web 专属坐标转换服务
 *
 * 提供 WGS-84 → GCJ-02（火星坐标系）坐标转换。
 * 仅用于地图渲染场景（高德地图要求 GCJ-02 坐标）。
 * 当前主要被 mock 数据使用；真实 API 返回的坐标已是 GCJ-02，无需转换。
 * Admin 应用不需要此服务。
 */
import type { Route, RouteList } from '@/types/route';

/** WGS-84 坐标转 GCJ-02（火星坐标系） */
const PI = Math.PI;
const A = 6378245.0;
const EE = 0.00669342162296594323;

function transformLat(lng: number, lat: number): number {
  let ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat +
    0.1 * lng * lat + 0.2 * Math.sqrt(Math.abs(lng));
  ret += (20.0 * Math.sin(6.0 * lng * PI) + 20.0 * Math.sin(2.0 * lng * PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(lat * PI) + 40.0 * Math.sin(lat / 3.0 * PI)) * 2.0 / 3.0;
  ret += (160.0 * Math.sin(lat / 12.0 * PI) + 320.0 * Math.sin(lat * PI / 30.0)) * 2.0 / 3.0;
  return ret;
}

function transformLng(lng: number, lat: number): number {
  let ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng +
    0.1 * lng * lat + 0.1 * Math.sqrt(Math.abs(lng));
  ret += (20.0 * Math.sin(6.0 * lng * PI) + 20.0 * Math.sin(2.0 * lng * PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(lng * PI) + 40.0 * Math.sin(lng / 3.0 * PI)) * 2.0 / 3.0;
  ret += (150.0 * Math.sin(lng / 12.0 * PI) + 300.0 * Math.sin(lng / 30.0 * PI)) * 2.0 / 3.0;
  return ret;
}

function wgs84ToGcj02(lng: number, lat: number): { lng: number; lat: number } {
  const dLat = transformLat(lng - 105.0, lat - 35.0);
  const dLng = transformLng(lng - 105.0, lat - 35.0);
  const radLat = (lat / 180.0) * PI;
  const magic = Math.sin(radLat);
  const sqrtMagic = Math.sqrt(1 - EE * magic * magic);
  const mgLat = lat + (dLat * 180.0) / (((A * (1 - EE)) / (sqrtMagic * sqrtMagic * sqrtMagic)) * PI);
  const mgLng = lng + (dLng * 180.0) / ((A / sqrtMagic) * Math.cos(radLat) * PI);
  return { lng: mgLng, lat: mgLat };
}

/** 将 Route 中的所有坐标从 WGS-84 批量转换为 GCJ-02 */
function convertRouteCoordinates(route: Route): Route {
  return {
    ...route,
    origin: { ...route.origin, ...wgs84ToGcj02(route.origin.lng, route.origin.lat) },
    destination: { ...route.destination, ...wgs84ToGcj02(route.destination.lng, route.destination.lat) },
    segs: route.segs.map((seg) => {
      if ('transfer' in seg) return seg;
      return {
        ...seg,
        origin: { ...seg.origin, ...wgs84ToGcj02(seg.origin.lng, seg.origin.lat) },
        destination: { ...seg.destination, ...wgs84ToGcj02(seg.destination.lng, seg.destination.lat) },
        stops: seg.stops.map((stop) => ({
          ...stop,
          station: { ...stop.station, ...wgs84ToGcj02(stop.station.lng, stop.station.lat) },
        })),
      };
    }),
    pathPoints: route.pathPoints.map(({ lng, lat }) => wgs84ToGcj02(lng, lat)),
  };
}

export function convertRouteListCoordinates(routes: RouteList): RouteList {
  return routes.map(convertRouteCoordinates);
}
