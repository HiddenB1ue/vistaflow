import { describe, expect, it } from 'vitest';
import {
  fetchAdminStations,
  fetchAdminTrainStops,
  fetchAdminTrains,
  updateAdminStationGeo,
} from './adminDataService';

describe('adminDataService', () => {
  it('fetchAdminStations returns paginated mock station data', async () => {
    const result = await fetchAdminStations({
      page: 1,
      pageSize: 2,
      keyword: '',
      geoStatus: 'all',
      geoSource: 'all',
      areaName: '',
      sortBy: 'updatedAt',
      sortOrder: 'desc',
    });

    expect(result.items.length).toBeLessThanOrEqual(2);
    expect(result.total).toBeGreaterThan(0);
    expect(result.items[0]).toHaveProperty('telecode');
  });

  it('updateAdminStationGeo updates mock station state', async () => {
    const updated = await updateAdminStationGeo('3', {
      longitude: 117.0354,
      latitude: 28.2412,
      geoSource: 'manual',
    });

    expect(updated.geoStatus).toBe('complete');
    expect(updated.longitude).toBe(117.0354);
  });

  it('fetchAdminTrains returns paginated mock train data', async () => {
    const result = await fetchAdminTrains({
      page: 1,
      pageSize: 10,
      keyword: '',
      isActive: 'all',
      sortBy: 'updatedAt',
      sortOrder: 'desc',
    });

    expect(result.total).toBeGreaterThan(0);
    expect(result.items[0]).toHaveProperty('trainNo');
  });

  it('fetchAdminTrainStops returns mock stop rows', async () => {
    const stops = await fetchAdminTrainStops('101');

    expect(Array.isArray(stops)).toBe(true);
    expect(stops[0]).toHaveProperty('stationNo');
  });
});
