import { beforeEach, describe, expect, it, vi, type Mock } from 'vitest';
import { apiClient } from './api';
import {
  fetchAdminStations,
  fetchAdminTrainStops,
  fetchAdminTrains,
  updateAdminStationGeo,
} from './adminDataService';
import type { AdminStationRecord, AdminTrainRecord, AdminTrainStopRecord } from '@/types/data';

vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

const sampleStation: AdminStationRecord = {
  id: '3',
  name: 'Yingtan',
  telecode: 'YTG',
  pinyin: null,
  abbr: null,
  areaName: null,
  countryName: null,
  longitude: null,
  latitude: null,
  geoSource: null,
  geoUpdatedAt: null,
  updatedAt: '2026-01-01T00:00:00Z',
  geoStatus: 'missing',
};

const sampleTrain: AdminTrainRecord = {
  id: '101',
  trainNo: 'G1',
  stationTrainCode: 'G1',
  fromStation: 'Beijing',
  toStation: 'Shanghai',
  totalNum: 2,
  isActive: true,
  updatedAt: '2026-01-01T00:00:00Z',
};

const sampleStop: AdminTrainStopRecord = {
  stationNo: 1,
  stationName: 'Beijing',
  stationTrainCode: 'G1',
  arriveTime: null,
  startTime: '09:00',
  runningTime: null,
  arriveDayDiff: 0,
  arriveDayStr: null,
  isStart: 'Y',
  startStationName: 'Beijing',
  endStationName: 'Shanghai',
  trainClassName: null,
  serviceType: null,
  wzNum: null,
  updatedAt: '2026-01-01T00:00:00Z',
};

describe('adminDataService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchAdminStations forwards query parameters to the API', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: {
        data: {
          items: [sampleStation],
          page: 1,
          pageSize: 2,
          total: 1,
          totalPages: 1,
        },
      },
    });

    const result = await fetchAdminStations({
      page: 1,
      pageSize: 2,
      keyword: ' ying ',
      geoStatus: 'all',
      geoSource: 'all',
      areaName: '',
      sortBy: 'updatedAt',
      sortOrder: 'desc',
    });

    expect(apiClient.get).toHaveBeenCalledWith('/admin/data/stations', {
      params: {
        page: 1,
        pageSize: 2,
        keyword: 'ying',
        geoStatus: 'all',
        geoSource: 'all',
        areaName: undefined,
        sortBy: 'updatedAt',
        sortOrder: 'desc',
      },
    });
    expect(result.items).toEqual([sampleStation]);
  });

  it('updateAdminStationGeo patches station coordinates', async () => {
    const updatedStation = {
      ...sampleStation,
      longitude: 117.0354,
      latitude: 28.2412,
      geoSource: 'manual' as const,
      geoStatus: 'complete' as const,
    };
    const payload = {
      longitude: 117.0354,
      latitude: 28.2412,
      geoSource: 'manual' as const,
    };
    (apiClient.patch as Mock).mockResolvedValueOnce({ data: { data: updatedStation } });

    const updated = await updateAdminStationGeo('3', {
      longitude: 117.0354,
      latitude: 28.2412,
      geoSource: 'manual',
    });

    expect(apiClient.patch).toHaveBeenCalledWith('/admin/data/stations/3/geo', payload);
    expect(updated.geoStatus).toBe('complete');
    expect(updated.longitude).toBe(117.0354);
  });

  it('fetchAdminTrains forwards query parameters to the API', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: {
        data: {
          items: [sampleTrain],
          page: 1,
          pageSize: 10,
          total: 1,
          totalPages: 1,
        },
      },
    });

    const result = await fetchAdminTrains({
      page: 1,
      pageSize: 10,
      keyword: ' G1 ',
      isActive: 'all',
      sortBy: 'updatedAt',
      sortOrder: 'desc',
    });

    expect(apiClient.get).toHaveBeenCalledWith('/admin/data/trains', {
      params: {
        page: 1,
        pageSize: 10,
        keyword: 'G1',
        isActive: 'all',
        sortBy: 'updatedAt',
        sortOrder: 'desc',
      },
    });
    expect(result.items).toEqual([sampleTrain]);
  });

  it('fetchAdminTrainStops unwraps stop rows from the API', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: { data: [sampleStop] } });

    const stops = await fetchAdminTrainStops('101');

    expect(apiClient.get).toHaveBeenCalledWith('/admin/data/trains/101/stops');
    expect(stops).toEqual([sampleStop]);
  });
});
