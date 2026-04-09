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
import {
  MOCK_ADMIN_STATIONS,
  MOCK_ADMIN_TRAINS,
  MOCK_ADMIN_TRAIN_STOPS,
} from './mock/data.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

function cloneStation(station: AdminStationRecord): AdminStationRecord {
  return { ...station };
}

function cloneTrain(train: AdminTrainRecord): AdminTrainRecord {
  return { ...train };
}

function cloneTrainStop(stop: AdminTrainStopRecord): AdminTrainStopRecord {
  return { ...stop };
}

function sortByString<T>(items: T[], getter: (item: T) => string, order: 'asc' | 'desc'): T[] {
  return [...items].sort((a, b) => {
    const left = getter(a);
    const right = getter(b);
    const compared = left.localeCompare(right, 'zh-CN');
    return order === 'asc' ? compared : -compared;
  });
}

function sortByNullableDate<T>(items: T[], getter: (item: T) => string | null, order: 'asc' | 'desc'): T[] {
  return [...items].sort((a, b) => {
    const leftRaw = getter(a);
    const rightRaw = getter(b);
    const left = leftRaw ? new Date(leftRaw).getTime() : (order === 'asc' ? Number.NEGATIVE_INFINITY : Number.POSITIVE_INFINITY);
    const right = rightRaw ? new Date(rightRaw).getTime() : (order === 'asc' ? Number.NEGATIVE_INFINITY : Number.POSITIVE_INFINITY);
    return order === 'asc' ? left - right : right - left;
  });
}

function paginate<T>(items: T[], page: number, pageSize: number): PaginatedResult<T> {
  const total = items.length;
  const totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);
  const safePage = totalPages === 0 ? 1 : Math.min(page, totalPages);
  const start = (safePage - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    page: safePage,
    pageSize,
    total,
    totalPages,
  };
}

let mockStationsState = MOCK_ADMIN_STATIONS.map(cloneStation);

export async function fetchAdminStations(
  query: AdminStationListQuery,
): Promise<PaginatedResult<AdminStationRecord>> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const keyword = query.keyword.trim().toLowerCase();
    const areaName = query.areaName.trim().toLowerCase();
    let filtered = mockStationsState.filter((station) => {
      const matchesKeyword =
        keyword.length === 0
        || [station.name, station.telecode, station.pinyin ?? '', station.abbr ?? '']
          .some((field) => field.toLowerCase().includes(keyword));
      const matchesGeoStatus = query.geoStatus === 'all' || station.geoStatus === query.geoStatus;
      const matchesGeoSource = query.geoSource === 'all' || station.geoSource === query.geoSource;
      const matchesAreaName = areaName.length === 0 || (station.areaName ?? '').toLowerCase().includes(areaName);
      return matchesKeyword && matchesGeoStatus && matchesGeoSource && matchesAreaName;
    });

    if (query.sortBy === 'name') {
      filtered = sortByString(filtered, (item) => item.name, query.sortOrder);
    } else if (query.sortBy === 'geoUpdatedAt') {
      filtered = sortByNullableDate(filtered, (item) => item.geoUpdatedAt, query.sortOrder);
    } else if (query.sortBy === 'id') {
      filtered = [...filtered].sort((a, b) => {
        const compared = Number(a.id) - Number(b.id);
        return query.sortOrder === 'asc' ? compared : -compared;
      });
    } else {
      filtered = sortByNullableDate(filtered, (item) => item.updatedAt, query.sortOrder);
    }

    const result = paginate(filtered.map(cloneStation), query.page, query.pageSize);
    return result;
  }

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
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 120));
    const existing = mockStationsState.find((station) => station.id === stationId);
    if (!existing) {
      throw new Error('Station not found');
    }
    const updated: AdminStationRecord = {
      ...existing,
      longitude: payload.longitude,
      latitude: payload.latitude,
      geoSource: payload.geoSource,
      geoUpdatedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      geoStatus:
        payload.longitude !== null && payload.latitude !== null ? 'complete' : 'missing',
    };
    mockStationsState = mockStationsState.map((station) =>
      station.id === stationId ? updated : station,
    );
    return cloneStation(updated);
  }

  const { data } = await apiClient.patch<{ data: AdminStationRecord }>(
    `/admin/data/stations/${stationId}/geo`,
    payload,
  );
  return data.data;
}

export async function fetchAdminTrains(
  query: AdminTrainListQuery,
): Promise<PaginatedResult<AdminTrainRecord>> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const keyword = query.keyword.trim().toLowerCase();
    let filtered = MOCK_ADMIN_TRAINS.filter((train) => {
      const matchesKeyword =
        keyword.length === 0
        || [train.trainNo, train.stationTrainCode ?? '', train.fromStation ?? '', train.toStation ?? '']
          .some((field) => field.toLowerCase().includes(keyword));
      const matchesIsActive =
        query.isActive === 'all'
        || (query.isActive === 'true' ? train.isActive : !train.isActive);
      return matchesKeyword && matchesIsActive;
    });

    if (query.sortBy === 'trainNo') {
      filtered = sortByString(filtered, (item) => item.trainNo, query.sortOrder);
    } else if (query.sortBy === 'stationTrainCode') {
      filtered = sortByString(filtered, (item) => item.stationTrainCode ?? '', query.sortOrder);
    } else if (query.sortBy === 'id') {
      filtered = [...filtered].sort((a, b) => {
        const compared = Number(a.id) - Number(b.id);
        return query.sortOrder === 'asc' ? compared : -compared;
      });
    } else {
      filtered = sortByNullableDate(filtered, (item) => item.updatedAt, query.sortOrder);
    }

    return paginate(filtered.map(cloneTrain), query.page, query.pageSize);
  }

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
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return (MOCK_ADMIN_TRAIN_STOPS[trainId] ?? []).map(cloneTrainStop);
  }
  const { data } = await apiClient.get<{ data: AdminTrainStopRecord[] }>(
    `/admin/data/trains/${trainId}/stops`,
  );
  return data.data;
}
