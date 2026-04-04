import { describe, it, expect } from 'vitest';
import { fetchStations } from './stationService';

describe('stationService', () => {
  it('fetchStations returns mock data in mock mode', async () => {
    const stations = await fetchStations();
    expect(Array.isArray(stations)).toBe(true);
    expect(stations.length).toBeGreaterThan(0);
    for (const station of stations) {
      expect(station).toHaveProperty('name');
      expect(station).toHaveProperty('code');
      expect(station).toHaveProperty('city');
    }
  });
});
