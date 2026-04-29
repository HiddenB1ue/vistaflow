import { describe, expect, it } from 'vitest';
import {
  buildGeoMap,
  collectStationNames,
  mapJourneyToRoute,
  type BackendJourneyResult,
  type BackendJourneySearchResponse,
  type BackendStationGeoResponse,
} from './journeyMapper';

describe('collectStationNames', () => {
  it('returns empty array for empty journeys', () => {
    const response: BackendJourneySearchResponse = { journeys: [], total: 0, date: '2026-04-04' };
    expect(collectStationNames(response)).toEqual([]);
  });

  it('collects unique station names from segments', () => {
    const response: BackendJourneySearchResponse = {
      journeys: [
        {
          id: 'j1',
          is_direct: true,
          total_duration_minutes: 278,
          departure_date: '2026-04-04',
          departure_time: '07:00',
          arrival_date: '2026-04-04',
          arrival_time: '11:38',
          min_price: 553,
          segments: [
            {
              train_code: 'G1',
              from_station: '北京南',
              to_station: '上海虹桥',
              departure_date: '2026-04-04',
              departure_time: '07:00',
              arrival_date: '2026-04-04',
              arrival_time: '11:38',
              duration_minutes: 278,
              stops_count: 0,
              seats: [],
            },
          ],
        },
      ],
      total: 1,
      date: '2026-04-04',
    };

    const names = collectStationNames(response);
    expect(names).toContain('北京南');
    expect(names).toContain('上海虹桥');
    expect(names).toHaveLength(2);
  });

  it('deduplicates station names across journeys', () => {
    const response: BackendJourneySearchResponse = {
      journeys: [
        {
          id: 'j1',
          is_direct: true,
          total_duration_minutes: 100,
          departure_date: '2026-04-04',
          departure_time: '07:00',
          arrival_date: '2026-04-04',
          arrival_time: '08:40',
          min_price: null,
          segments: [
            { train_code: 'G1', from_station: 'A', to_station: 'B', departure_date: '2026-04-04', departure_time: '07:00', arrival_date: '2026-04-04', arrival_time: '08:40', duration_minutes: 100, stops_count: 0, seats: [] },
          ],
        },
        {
          id: 'j2',
          is_direct: false,
          total_duration_minutes: 200,
          departure_date: '2026-04-04',
          departure_time: '09:00',
          arrival_date: '2026-04-05',
          arrival_time: '12:20',
          min_price: null,
          segments: [
            { train_code: 'G2', from_station: 'A', to_station: 'C', departure_date: '2026-04-04', departure_time: '09:00', arrival_date: '2026-04-04', arrival_time: '10:30', duration_minutes: 90, stops_count: 0, seats: [] },
            { train_code: 'G3', from_station: 'C', to_station: 'B', departure_date: '2026-04-05', departure_time: '11:00', arrival_date: '2026-04-05', arrival_time: '12:20', duration_minutes: 80, stops_count: 0, seats: [] },
          ],
        },
      ],
      total: 2,
      date: '2026-04-04',
    };

    const names = collectStationNames(response);
    expect(new Set(names).size).toBe(names.length);
    expect(names).toContain('A');
    expect(names).toContain('B');
    expect(names).toContain('C');
    expect(names).toHaveLength(3);
  });
});

describe('buildGeoMap', () => {
  it('builds map from geo response', () => {
    const response: BackendStationGeoResponse = {
      items: [
        { name: '北京南', longitude: 116.3783, latitude: 39.8654, found: true },
        { name: '未知站', longitude: null, latitude: null, found: false },
      ],
    };
    const map = buildGeoMap(response);
    expect(map.get('北京南')).toEqual({ lng: 116.3783, lat: 39.8654 });
    expect(map.has('未知站')).toBe(false);
  });
});

describe('mapJourneyToRoute', () => {
  it('maps a direct journey correctly', () => {
    const journey: BackendJourneyResult = {
      id: 'G1',
      is_direct: true,
      total_duration_minutes: 278,
      departure_date: '2026-04-04',
      departure_time: '07:00',
      arrival_date: '2026-04-04',
      arrival_time: '11:38',
      min_price: 553,
      segments: [
        {
          train_code: 'G1',
          from_station: '北京南',
          to_station: '上海虹桥',
          departure_date: '2026-04-04',
          departure_time: '07:00',
          arrival_date: '2026-04-04',
          arrival_time: '11:38',
          duration_minutes: 278,
          stops_count: 0,
          seats: [
            { seat_type: 'ze', status: 'available', price: 553, available: true },
            { seat_type: 'zy', status: 'available', price: 933, available: true },
          ],
        },
      ],
    };
    const geoMap = new Map([
      ['北京南', { lng: 116.3783, lat: 39.8654 }],
      ['上海虹桥', { lng: 121.322, lat: 31.1945 }],
    ]);

    const route = mapJourneyToRoute(journey, geoMap);
    expect(route.id).toBe('G1');
    expect(route.type).toBe('直达');
    expect(route.durationMinutes).toBe(278);
    expect(route.departureDate).toBe('2026-04-04');
    expect(route.arrivalDate).toBe('2026-04-04');
    expect(route.segs).toHaveLength(1);
    expect(route.pathPoints).toHaveLength(2);
  });

  it('preserves raw 12306 seat types', () => {
    const journey: BackendJourneyResult = {
      id: 'G2',
      is_direct: true,
      total_duration_minutes: 278,
      departure_date: '2026-04-04',
      departure_time: '07:00',
      arrival_date: '2026-04-04',
      arrival_time: '11:38',
      min_price: 553,
      segments: [
        {
          train_code: 'G2',
          from_station: '北京南',
          to_station: '上海虹桥',
          departure_date: '2026-04-04',
          departure_time: '07:00',
          arrival_date: '2026-04-04',
          arrival_time: '11:38',
          duration_minutes: 278,
          stops_count: 0,
          seats: [
            { seat_type: 'swz', status: '无', price: 1748, available: false },
            { seat_type: 'wz', status: '有', price: 553, available: true },
          ],
        },
      ],
    };
    const geoMap = new Map([
      ['北京南', { lng: 116.3783, lat: 39.8654 }],
      ['上海虹桥', { lng: 121.322, lat: 31.1945 }],
    ]);

    const route = mapJourneyToRoute(journey, geoMap);
    const segment = route.segs[0];
    if ('transfer' in segment) {
      throw new Error('expected train segment');
    }
    expect(segment.seats).toEqual([
      { type: 'swz', label: '商务座', price: 1748, available: false, availabilityText: '无' },
      { type: 'wz', label: '无座', price: 553, available: true, availabilityText: '有' },
    ]);
  });
});
