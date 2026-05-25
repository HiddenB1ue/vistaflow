import type { JourneyViewPrefs } from '@/stores/uiStore';
import type { Route, TrainSegment } from '@/types/route';
import { isTransfer } from '@/types/route';
import type { SearchParams } from '@/types/search';
import { apiClient } from './api';

export type JourneySortMode = 'duration' | 'departure' | 'price';
export type JourneyDisplaySortMode = JourneySortMode;

export interface JourneyAvailableFacets {
  transferCounts: number[];
  trainTypes: string[];
}

export interface JourneyViewRequest {
  sort_by: JourneySortMode;
  exclude_direct_train_codes_in_transfer_routes: boolean;
  display_train_types: string[];
  transfer_counts: number[];
  page: number;
  page_size: number;
  include_tickets: boolean;
}

export interface JourneyViewResult {
  items: Route[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  appliedView: {
    sortBy: JourneySortMode;
    excludeDirectTrainCodesInTransferRoutes: boolean;
    displayTrainTypes: string[];
    transferCounts: number[];
    page: number;
    pageSize: number;
    includeTickets: boolean;
  };
  availableFacets: JourneyAvailableFacets;
}

export interface JourneySearchSessionResult {
  searchId: string;
  searchSummary: {
    fromStation: string;
    toStation: string;
    date: string;
    totalCandidates: number;
  };
  viewResult: JourneyViewResult;
}

function normalizeStationName(name: string): string {
  return name.endsWith('站') ? name.slice(0, -1) : name;
}

export function buildJourneyViewRequest(
  filterPrefs: JourneyViewPrefs,
  sortMode: JourneySortMode,
  page: number,
  pageSize: number,
): JourneyViewRequest {
  return {
    sort_by: sortMode,
    exclude_direct_train_codes_in_transfer_routes:
      filterPrefs.excludeDirectTrainCodesInTransferRoutes,
    display_train_types: filterPrefs.displayTrainTypes,
    transfer_counts: filterPrefs.transferCounts,
    page,
    page_size: pageSize,
    include_tickets: true,
  };
}

export async function createJourneySearchSession(
  params: SearchParams,
): Promise<JourneySearchSessionResult> {
  const initialView = buildJourneyViewRequest(
    {
      excludeDirectTrainCodesInTransferRoutes: false,
      displayTrainTypes: [],
      transferCounts: [],
      showOnlyAvailableTickets: false,
    },
    'duration',
    1,
    20,
  );

  const { data } = await apiClient.post<{ data: JourneySearchSessionResult }>(
    '/journey-search-sessions',
    {
      from_station: normalizeStationName(params.origin),
      to_station: normalizeStationName(params.destination),
      date: params.date,
      transfer_count: params.transferCount,
      include_fewer_transfers: true,
      allowed_train_types: params.allowedTrainTypes,
      excluded_train_types: params.excludedTrainTypes,
      allowed_trains: params.allowedTrains,
      excluded_trains: params.excludedTrains,
      departure_time_start: params.departureTimeStart || undefined,
      departure_time_end: params.departureTimeEnd || undefined,
      arrival_deadline: params.arrivalDeadline || undefined,
      min_transfer_minutes: params.minTransferMinutes,
      max_transfer_minutes: params.maxTransferMinutes
        ? Number(params.maxTransferMinutes)
        : undefined,
      allowed_transfer_stations: params.allowedTransferStations,
      excluded_transfer_stations: params.excludedTransferStations,
      filter_running_only: true,
      view: initialView,
    },
  );
  return data.data;
}

export async function fetchJourneySearchSessionView(
  searchId: string,
  request: JourneyViewRequest,
): Promise<JourneyViewResult> {
  const { data } = await apiClient.post<{ data: JourneyViewResult }>(
    `/journey-search-sessions/${encodeURIComponent(searchId)}/view`,
    request,
  );
  return data.data;
}

export interface RouteStopGeo {
  name: string;
  lng: number;
  lat: number;
}

async function fetchSegmentStops(
  seg: TrainSegment,
): Promise<Array<{ station_name: string; longitude: number | null; latitude: number | null }>> {
  const { data } = await apiClient.get<{
    data: {
      train_code: string;
      stops: Array<{
        station_name: string;
        stop_number: number;
        longitude: number | null;
        latitude: number | null;
      }>;
    };
  }>(
    `/trains/${encodeURIComponent(seg.no)}/stops`,
    {
      params: {
        from_station: seg.origin.name,
        to_station: seg.destination.name,
      },
    },
  );
  return data.data.stops;
}

export async function fetchRouteStopsGeo(route: Route): Promise<RouteStopGeo[]> {
  const trainSegs = route.segs.filter(
    (s): s is TrainSegment => !isTransfer(s),
  );
  const allStops: RouteStopGeo[] = [];
  const seen = new Set<string>();

  for (const seg of trainSegs) {
    try {
      const stops = await fetchSegmentStops(seg);
      for (const stop of stops) {
        if (seen.has(stop.station_name)) continue;
        seen.add(stop.station_name);
        if (stop.longitude != null && stop.latitude != null) {
          allStops.push({
            name: stop.station_name,
            lng: stop.longitude,
            lat: stop.latitude,
          });
        }
      }
    } catch {
      // Skip if stops fetch fails for a segment.
    }
  }

  return allStops;
}
