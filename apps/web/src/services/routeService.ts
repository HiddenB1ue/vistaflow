import type { JourneyViewPrefs } from '@/stores/uiStore';
import type { RouteList } from '@/types/route';
import type { SearchParams } from '@/types/search';
import { apiClient } from './api';
import { mockRoutes } from './mock/routes.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export type JourneySortMode = 'duration' | 'departure';
export type JourneyDisplaySortMode = JourneySortMode | 'price';

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
  items: RouteList;
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
  expiresAt: string;
  searchSummary: {
    fromStation: string;
    toStation: string;
    date: string;
    totalCandidates: number;
  };
  viewResult: JourneyViewResult;
}

const mockSessions = new Map<string, RouteList>();

function normalizeStationName(name: string): string {
  return name.endsWith('站') ? name.slice(0, -1) : name;
}

function getTrainTypes(route: RouteList[number]): string[] {
  return route.segs
    .flatMap((segment) =>
      'transfer' in segment ? [] : [segment.no.trim().toUpperCase().slice(0, 1)],
    )
    .filter(Boolean);
}

function getTrainCodes(route: RouteList[number]): string[] {
  return route.segs.flatMap((segment) =>
    'transfer' in segment ? [] : [segment.no.trim().toUpperCase()],
  );
}

function getTransferCount(route: RouteList[number]): number {
  return route.segs.filter((segment) => 'transfer' in segment).length;
}

function isDirectRoute(route: RouteList[number]): boolean {
  return getTransferCount(route) === 0;
}

function buildAvailableFacets(routes: RouteList): JourneyAvailableFacets {
  return {
    transferCounts: [...new Set(routes.map((route) => getTransferCount(route)))].sort(
      (a, b) => a - b,
    ),
    trainTypes: [...new Set(routes.flatMap((route) => getTrainTypes(route)))].sort(),
  };
}

function applyMockView(routes: RouteList, request: JourneyViewRequest): JourneyViewResult {
  const availableFacets = buildAvailableFacets(routes);
  let nextRoutes = [...routes];

  if (request.transfer_counts.length > 0) {
    const allowedTransferCounts = new Set(request.transfer_counts);
    nextRoutes = nextRoutes.filter((route) =>
      allowedTransferCounts.has(getTransferCount(route)),
    );
  }

  if (request.exclude_direct_train_codes_in_transfer_routes) {
    const directCodes = new Set(
      routes.flatMap((route) => (isDirectRoute(route) ? getTrainCodes(route) : [])),
    );
    nextRoutes = nextRoutes.filter(
      (route) =>
        isDirectRoute(route) ||
        getTrainCodes(route).every((code) => !directCodes.has(code)),
    );
  }

  if (request.display_train_types.length > 0) {
    const allowedTypes = new Set(
      request.display_train_types.map((item) => item.trim().toUpperCase()),
    );
    nextRoutes = nextRoutes.filter((route) =>
      getTrainTypes(route).every((trainType) => allowedTypes.has(trainType)),
    );
  }

  if (request.sort_by === 'departure') {
    nextRoutes.sort((a, b) => a.departureTime.localeCompare(b.departureTime));
  } else {
    nextRoutes.sort((a, b) => a.durationMinutes - b.durationMinutes);
  }

  const total = nextRoutes.length;
  const start = (request.page - 1) * request.page_size;
  const items = nextRoutes.slice(start, start + request.page_size);
  return {
    items,
    total,
    page: request.page,
    pageSize: request.page_size,
    totalPages: total === 0 ? 0 : Math.ceil(total / request.page_size),
    appliedView: {
      sortBy: request.sort_by,
      excludeDirectTrainCodesInTransferRoutes:
        request.exclude_direct_train_codes_in_transfer_routes,
      displayTrainTypes: [...request.display_train_types],
      transferCounts: [...request.transfer_counts].sort((a, b) => a - b),
      page: request.page,
      pageSize: request.page_size,
      includeTickets: request.include_tickets,
    },
    availableFacets,
  };
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
    },
    'duration',
    1,
    20,
  );

  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 200));
    const searchId = `mock-${Date.now()}`;
    mockSessions.set(searchId, mockRoutes);
    return {
      searchId,
      expiresAt: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
      searchSummary: {
        fromStation: params.origin,
        toStation: params.destination,
        date: params.date,
        totalCandidates: mockRoutes.length,
      },
      viewResult: applyMockView(mockRoutes, initialView),
    };
  }

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
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return applyMockView(mockSessions.get(searchId) ?? mockRoutes, request);
  }

  const { data } = await apiClient.post<{ data: JourneyViewResult }>(
    `/journey-search-sessions/${encodeURIComponent(searchId)}/view`,
    request,
  );
  return data.data;
}
