import type { RouteList } from '@/types/route';
import type { SearchParams } from '@/types/search';
import { apiClient } from './api';
import {
  type BackendJourneySearchResponse,
  type BackendStationGeoResponse,
  collectStationNames,
  mapJourneysToRoutes,
} from './journeyMapper';
import { mockRoutes } from './mock/routes.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

/**
 * 移除车站名称末尾的"站"字
 */
function normalizeStationName(name: string): string {
  return name.endsWith('站') ? name.slice(0, -1) : name;
}

async function fetchStationGeo(names: string[]): Promise<BackendStationGeoResponse> {
  if (names.length === 0) return { items: [] };
  const params = new URLSearchParams();
  names.forEach((n) => params.append('names', n));
  const { data } = await apiClient.get<{ data: BackendStationGeoResponse }>(
    `/stations?${params.toString()}`,
  );
  return data.data;
}

export async function fetchRoutes(params: SearchParams): Promise<RouteList> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 800));
    return mockRoutes;
  }

  const { data: searchResp } = await apiClient.post<{ data: BackendJourneySearchResponse }>(
    '/journeys/search',
    {
      from_station: normalizeStationName(params.origin),
      to_station:   normalizeStationName(params.destination),
      date:         params.date,
      transfer_count: 1,
      include_fewer_transfers: true,
      enable_ticket_enrich: false,
    },
  );

  const searchData = searchResp.data;

  const stationNames = collectStationNames(searchData);
  const geoData = await fetchStationGeo(stationNames);

  return mapJourneysToRoutes(searchData, geoData);
}
