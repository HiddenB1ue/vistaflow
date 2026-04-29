
import type { Route, RouteList, RouteSegment, SeatClass, Station, TrainSegment } from '@/types/route';
import { getSeatLabel } from '@/utils/seat';
import type {
  BackendJourneyResult,
  BackendJourneySearchResponse,
  BackendJourneySegment,
  BackendSeatSchema,
  BackendStationGeoResponse,
} from './journeyMapper.types';

function mapSeats(rawSeats: BackendSeatSchema[]): SeatClass[] {
  return rawSeats.map((raw) => ({
    type: raw.seat_type,
    label: getSeatLabel(raw.seat_type),
    price: raw.price,
    available: raw.available,
    availabilityText: raw.status || undefined,
  }));
}

function buildStation(name: string, geoMap: Map<string, { lng: number; lat: number }>): Station {
  const geo = geoMap.get(name);
  return {
    name,
    code: '',
    city: '',
    lng: geo?.lng ?? 0,
    lat: geo?.lat ?? 0,
  };
}

function routeTypeLabel(result: BackendJourneyResult): string {
  if (result.is_direct) return '直达';
  const transfers = result.segments.length - 1;
  return transfers === 1 ? '中转 1 次' : `中转 ${transfers} 次`;
}

function buildTrainSegment(
  segment: BackendJourneySegment,
  geoMap: Map<string, { lng: number; lat: number }>,
): TrainSegment {
  return {
    trainNo: segment.train_code,
    no: segment.train_code,
    origin: buildStation(segment.from_station, geoMap),
    destination: buildStation(segment.to_station, geoMap),
    departureDate: segment.departure_date,
    departureTime: segment.departure_time,
    arrivalDate: segment.arrival_date,
    arrivalTime: segment.arrival_time,
    stops: [], // 初始为空，按需加载
    stopsCount: segment.stops_count, // 经停数量
    seats: mapSeats(segment.seats),
  };
}

function buildRouteSegments(
  segments: BackendJourneySegment[],
  geoMap: Map<string, { lng: number; lat: number }>,
): RouteSegment[] {
  const routeSegments: RouteSegment[] = [];

  for (let index = 0; index < segments.length; index += 1) {
    routeSegments.push(buildTrainSegment(segments[index], geoMap));

    if (index < segments.length - 1) {
      const currentSegment = segments[index];
      const nextSegment = segments[index + 1];
      routeSegments.push({
        transfer: `${currentSegment.to_station} 换乘 ${nextSegment.train_code}`,
      });
    }
  }

  return routeSegments;
}

function buildPathPoints(
  segments: BackendJourneySegment[],
  geoMap: Map<string, { lng: number; lat: number }>,
): Array<{ lng: number; lat: number }> {
  const points: Array<{ lng: number; lat: number }> = [];
  const seen = new Set<string>();

  const addPoint = (name: string) => {
    if (seen.has(name)) return;
    seen.add(name);
    const geo = geoMap.get(name);
    if (geo) points.push(geo);
  };

  for (const segment of segments) {
    addPoint(segment.from_station);
    addPoint(segment.to_station);
  }

  return points;
}

export function mapJourneyToRoute(
  result: BackendJourneyResult,
  geoMap: Map<string, { lng: number; lat: number }>,
): Route {
  const firstSegment = result.segments[0];
  const lastSegment = result.segments[result.segments.length - 1];

  return {
    id: result.id,
    trainNo: result.segments.map((segment) => segment.train_code).join(' / '),
    type: routeTypeLabel(result),
    origin: buildStation(firstSegment.from_station, geoMap),
    destination: buildStation(lastSegment.to_station, geoMap),
    departureDate: result.departure_date,
    departureTime: result.departure_time,
    arrivalDate: result.arrival_date,
    arrivalTime: result.arrival_time,
    durationMinutes: result.total_duration_minutes,
    segs: buildRouteSegments(result.segments, geoMap),
    pathPoints: buildPathPoints(result.segments, geoMap),
  };
}

export function buildGeoMap(geoResponse: BackendStationGeoResponse): Map<string, { lng: number; lat: number }> {
  const map = new Map<string, { lng: number; lat: number }>();
  for (const item of geoResponse.items) {
    if (item.found && item.longitude !== null && item.latitude !== null) {
      map.set(item.name, { lng: item.longitude, lat: item.latitude });
    }
  }
  return map;
}

export function mapJourneysToRoutes(
  searchResponse: BackendJourneySearchResponse,
  geoResponse: BackendStationGeoResponse,
): RouteList {
  const geoMap = buildGeoMap(geoResponse);
  return searchResponse.journeys.map((journey) => mapJourneyToRoute(journey, geoMap));
}

export function collectStationNames(searchResponse: BackendJourneySearchResponse): string[] {
  const names = new Set<string>();
  for (const journey of searchResponse.journeys) {
    for (const segment of journey.segments) {
      names.add(segment.from_station);
      names.add(segment.to_station);
    }
  }
  return Array.from(names);
}
