import type { Route, RouteList } from '@/types/route';

const PI = Math.PI;
const A = 6378245.0;
const EE = 0.00669342162296594323;

function transformLat(lng: number, lat: number): number {
  let ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat
    + 0.1 * lng * lat + 0.2 * Math.sqrt(Math.abs(lng));
  ret += (20.0 * Math.sin(6.0 * lng * PI) + 20.0 * Math.sin(2.0 * lng * PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(lat * PI) + 40.0 * Math.sin(lat / 3.0 * PI)) * 2.0 / 3.0;
  ret += (160.0 * Math.sin(lat / 12.0 * PI) + 320.0 * Math.sin(lat * PI / 30.0)) * 2.0 / 3.0;
  return ret;
}

function transformLng(lng: number, lat: number): number {
  let ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng
    + 0.1 * lng * lat + 0.1 * Math.sqrt(Math.abs(lng));
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

function gcj02ToWgs84(gcjLng: number, gcjLat: number): { lng: number; lat: number } {
  let wgsLng = gcjLng;
  let wgsLat = gcjLat;
  for (let i = 0; i < 3; i += 1) {
    const { lng: mgLng, lat: mgLat } = wgs84ToGcj02(wgsLng, wgsLat);
    wgsLng += gcjLng - mgLng;
    wgsLat += gcjLat - mgLat;
  }
  return { lng: wgsLng, lat: wgsLat };
}

export function convertPointToWgs84(point: { lng: number; lat: number }): { lng: number; lat: number } {
  return gcj02ToWgs84(point.lng, point.lat);
}

function convertRouteToWgs84(route: Route): Route {
  return {
    ...route,
    origin: { ...route.origin, ...gcj02ToWgs84(route.origin.lng, route.origin.lat) },
    destination: { ...route.destination, ...gcj02ToWgs84(route.destination.lng, route.destination.lat) },
    segs: route.segs.map((seg) => {
      if ('transfer' in seg) return seg;
      return {
        ...seg,
        origin: { ...seg.origin, ...gcj02ToWgs84(seg.origin.lng, seg.origin.lat) },
        destination: { ...seg.destination, ...gcj02ToWgs84(seg.destination.lng, seg.destination.lat) },
        stops: seg.stops.map((stop) => ({
          ...stop,
          station: { ...stop.station, ...gcj02ToWgs84(stop.station.lng, stop.station.lat) },
        })),
      };
    }),
    pathPoints: route.pathPoints.map(({ lng, lat }) => gcj02ToWgs84(lng, lat)),
  };
}

export function convertRouteListToWgs84(routes: RouteList): RouteList {
  return routes.map(convertRouteToWgs84);
}
