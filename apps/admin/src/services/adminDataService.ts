import type {
  AdminStationGeoUpdatePayload,
  AdminStationListQuery,
  AdminStationRecord,
  AdminTrainListQuery,
  AdminTrainRecord,
  AdminTrainStopRecord,
  PaginatedResult,
} from '@/types/data';
import { apiClient } from './api';

export async function fetchAdminStations(
  query: AdminStationListQuery,
): Promise<PaginatedResult<AdminStationRecord>> {
  const { data } = await apiClient.get<{ data: PaginatedResult<AdminStationRecord> }>(
    '/admin/data/stations',
    {
      params: {
        page: query.page,
        pageSize: query.pageSize,
        keyword: query.keyword.trim() || undefined,
        geoStatus: query.geoStatus,
        geoSource: query.geoSource,
        areaName: query.areaName.trim() || undefined,
        sortBy: query.sortBy,
        sortOrder: query.sortOrder,
      },
    },
  );
  return data.data;
}

export async function updateAdminStationGeo(
  stationId: string,
  payload: AdminStationGeoUpdatePayload,
): Promise<AdminStationRecord> {
  const { data } = await apiClient.patch<{ data: AdminStationRecord }>(
    `/admin/data/stations/${stationId}/geo`,
    payload,
  );
  return data.data;
}

export async function fetchAdminTrains(
  query: AdminTrainListQuery,
): Promise<PaginatedResult<AdminTrainRecord>> {
  const { data } = await apiClient.get<{ data: PaginatedResult<AdminTrainRecord> }>(
    '/admin/data/trains',
    {
      params: {
        page: query.page,
        pageSize: query.pageSize,
        keyword: query.keyword.trim() || undefined,
        isActive: query.isActive,
        sortBy: query.sortBy,
        sortOrder: query.sortOrder,
      },
    },
  );
  return data.data;
}

export async function fetchAdminTrainStops(trainId: string): Promise<AdminTrainStopRecord[]> {
  const { data } = await apiClient.get<{ data: AdminTrainStopRecord[] }>(
    `/admin/data/trains/${trainId}/stops`,
  );
  return data.data;
}
