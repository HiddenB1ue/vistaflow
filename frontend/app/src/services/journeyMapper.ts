/**
 * journeyMapper.ts
 *
 * Converts backend JourneySearchResponse + StationGeoResponse into
 * the frontend Route[] shape defined in types/route.ts.
 *
 * Rules:
 * - Backend station coords are already GCJ-02, no conversion needed.
 * - Seats may be empty when enable_ticket_enrich=false; handled gracefully.
 * - TransferSegment nodes are inserted between consecutive JourneySegments.
 */

import type { Route, RouteList, RouteSegment, SeatClass, Station, TrainSegment } from '@/types/route';

// ─── Backend response shapes (mirrors backend Pydantic schemas) ───────────────

export interface BackendSeatSchema {
  seat_type: string;
  status: string;
  price: number | null;
  available: boolean;
}

export interface BackendJourneySegment {
  train_code: string;
  from_station: string;
  to_station: string;
  departure_time: string;  // "HH:mm"
  arrival_time: string;    // "HH:mm"
  duration_minutes: number;
  seats: BackendSeatSchema[];
}

export interface BackendJourneyResult {
  id: string;
  is_direct: boolean;
  total_duration_minutes: number;
  departure_time: string;
  arrival_time: string;
  min_price: number | null;
  segments: BackendJourneySegment[];
}

export interface BackendJourneySearchResponse {
  journeys: BackendJourneyResult[];
  total: number;
  date: string;
}

export interface BackendStationGeoItem {
  name: string;
  longitude: number | null;
  latitude: number | null;
  found: boolean;
}

export interface BackendStationGeoResponse {
  items: BackendStationGeoItem[];
}

// ─── Seat type mapping ────────────────────────────────────────────────────────

/**
 * 12306 seat_type codes → frontend SeatClass.type.
 * Covers both full codes (swz, zy, ze) and common variants.
 */
const SEAT_TYPE_MAP: Record<string, SeatClass['type']> = {
  swz: 'business',   // 商务座
  tz:  'business',   // 特等座 (treated as business)
  gr:  'business',   // 高级软卧
  zy:  'first',      // 一等座
  ze:  'second',     // 二等座
  rz:  'second',     // 软座
  yz:  'second',     // 硬座
};

const SEAT_LABELS: Record<SeatClass['type'], string> = {
  business: '商务座',
  first:    '一等座',
  second:   '二等座',
};

function mapSeatType(raw: string): SeatClass['type'] | null {
  const key = raw.toLowerCase().trim();
  return SEAT_TYPE_MAP[key] ?? null;
}

function mapSeats(rawSeats: BackendSeatSchema[]): SeatClass[] {
  const seen = new Set<SeatClass['type']>();
  const result: SeatClass[] = [];

  for (const raw of rawSeats) {
    const type = mapSeatType(raw.seat_type);
    if (!type || seen.has(type)) continue;
    seen.add(type);
    result.push({
      type,
      label:     SEAT_LABELS[type],
      price:     raw.price ?? 0,
      available: raw.available,
    });
  }

  // Stable order: business → first → second
  const ORDER: SeatClass['type'][] = ['business', 'first', 'second'];
  return result.sort((a, b) => ORDER.indexOf(a.type) - ORDER.indexOf(b.type));
}

// ─── Station builder ──────────────────────────────────────────────────────────

function buildStation(
  name: string,
  geoMap: Map<string, { lng: number; lat: number }>,
): Station {
  const geo = geoMap.get(name);
  return {
    name,
    code: '',          // telecode not provided in journey search response
    city: '',          // city not provided; could be enriched later
    lng:  geo?.lng ?? 0,
    lat:  geo?.lat ?? 0,
  };
}

// ─── Route type label ─────────────────────────────────────────────────────────

function routeTypeLabel(result: BackendJourneyResult): string {
  if (result.is_direct) return '直达';
  const transfers = result.segments.length - 1;
  return transfers === 1 ? '中转 1 次' : `中转 ${transfers} 次`;
}

// ─── Segment assembly ─────────────────────────────────────────────────────────

function buildTrainSegment(
  seg: BackendJourneySegment,
  geoMap: Map<string, { lng: number; lat: number }>,
): TrainSegment {
  return {
    no:            seg.train_code,
    origin:        buildStation(seg.from_station, geoMap),
    destination:   buildStation(seg.to_station, geoMap),
    departureTime: seg.departure_time,
    arrivalTime:   seg.arrival_time,
    stops:         [],   // detailed stops loaded on-demand via GET /api/trains/:code/stops
    seats:         mapSeats(seg.seats),
  };
}

function buildRouteSegs(
  segments: BackendJourneySegment[],
  geoMap: Map<string, { lng: number; lat: number }>,
): RouteSegment[] {
  const segs: RouteSegment[] = [];

  for (let i = 0; i < segments.length; i++) {
    segs.push(buildTrainSegment(segments[i], geoMap));

    if (i < segments.length - 1) {
      const cur  = segments[i];
      const next = segments[i + 1];
      segs.push({
        transfer: `${cur.to_station} 换乘 ${next.train_code}`,
      });
    }
  }

  return segs;
}

// ─── pathPoints assembly ──────────────────────────────────────────────────────

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

  for (const seg of segments) {
    addPoint(seg.from_station);
    addPoint(seg.to_station);
  }

  return points;
}

// ─── Main mapper ──────────────────────────────────────────────────────────────

export function mapJourneyToRoute(
  result: BackendJourneyResult,
  geoMap: Map<string, { lng: number; lat: number }>,
): Route {
  const firstSeg = result.segments[0];
  const lastSeg  = result.segments[result.segments.length - 1];

  const trainNoParts = result.segments.map((s) => s.train_code);
  const trainNo      = trainNoParts.join(' / ');

  return {
    id:              result.id,
    trainNo,
    type:            routeTypeLabel(result),
    origin:          buildStation(firstSeg.from_station, geoMap),
    destination:     buildStation(lastSeg.to_station, geoMap),
    departureTime:   result.departure_time,
    arrivalTime:     result.arrival_time,
    durationMinutes: result.total_duration_minutes,
    segs:            buildRouteSegs(result.segments, geoMap),
    pathPoints:      buildPathPoints(result.segments, geoMap),
  };
}

export function buildGeoMap(
  geoResponse: BackendStationGeoResponse,
): Map<string, { lng: number; lat: number }> {
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
  return searchResponse.journeys.map((j) => mapJourneyToRoute(j, geoMap));
}

/** Extract all unique station names from a journey search response. */
export function collectStationNames(
  searchResponse: BackendJourneySearchResponse,
): string[] {
  const names = new Set<string>();
  for (const journey of searchResponse.journeys) {
    for (const seg of journey.segments) {
      names.add(seg.from_station);
      names.add(seg.to_station);
    }
  }
  return Array.from(names);
}
