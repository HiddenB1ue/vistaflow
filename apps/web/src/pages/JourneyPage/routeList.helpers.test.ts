import { describe, expect, it } from 'vitest';
import { routeFixtures } from '@/services/mock/routeFixtures';
import {
  getNextSelectedRoute,
  getCollapsedRouteSummary,
  routeHasAvailableTickets,
  sortRoutesForDisplay,
} from './routeList.helpers';

describe('sortRoutesForDisplay', () => {
  it('sorts routes by summed per-segment reference price on the current result set', () => {
    const sorted = sortRoutesForDisplay(routeFixtures, 'price');

    expect(sorted.map((route) => route.id)).toEqual([
      'G101',
      'G1',
      'G107',
      'G105-R',
      'G21',
      'G103',
    ]);
  });

  it('pushes routes without a full reference price to the end', () => {
    const unavailableRoute = {
      ...routeFixtures[0],
      id: 'no-price',
      segs: routeFixtures[0].segs.map((segment) =>
        'transfer' in segment
          ? segment
          : {
              ...segment,
              seats: segment.seats.map((seat) => ({
                ...seat,
                available: false,
              })),
            },
      ),
    };

    const sorted = sortRoutesForDisplay([unavailableRoute, routeFixtures[3], routeFixtures[0]], 'price');

    expect(sorted.map((route) => route.id)).toEqual(['G1', 'G105-R', 'no-price']);
  });
});

describe('routeHasAvailableTickets', () => {
  it('returns true when every train segment has at least one available seat', () => {
    expect(routeHasAvailableTickets(routeFixtures[0])).toBe(true);
    expect(routeHasAvailableTickets(routeFixtures[3])).toBe(true);
  });

  it('returns false when any train segment has no available seats', () => {
    const unavailableRoute = {
      ...routeFixtures[3],
      segs: routeFixtures[3].segs.map((segment, index) =>
        index !== 2 || 'transfer' in segment
          ? segment
          : {
              ...segment,
              seats: segment.seats.map((seat) => ({
                ...seat,
                available: false,
              })),
            },
      ),
    };

    expect(routeHasAvailableTickets(unavailableRoute)).toBe(false);
  });
});

describe('getNextSelectedRoute', () => {
  it('selects a route when nothing is selected', () => {
    expect(getNextSelectedRoute(null, routeFixtures[0])).toBe(routeFixtures[0]);
  });

  it('clears selection when clicking the selected route again', () => {
    expect(getNextSelectedRoute(routeFixtures[0], routeFixtures[0])).toBeNull();
  });

  it('switches selection when clicking a different route', () => {
    expect(getNextSelectedRoute(routeFixtures[0], routeFixtures[1])).toBe(routeFixtures[1]);
  });
});

describe('getCollapsedRouteSummary', () => {
  it('returns train badges and endpoints for direct routes', () => {
    expect(getCollapsedRouteSummary(routeFixtures[0])).toEqual({
      kind: 'direct',
      trainCodes: ['G1'],
      transferStations: [],
      endpoints: '北京南 → 上海虹桥',
    });
  });

  it('returns train badges and transfer badges for transfer routes', () => {
    expect(getCollapsedRouteSummary(routeFixtures[3])).toEqual({
      kind: 'transfer',
      trainCodes: ['G105', 'G213'],
      transferStations: ['济南西换乘'],
      endpoints: null,
    });

    expect(getCollapsedRouteSummary(routeFixtures[5])).toEqual({
      kind: 'transfer',
      trainCodes: ['G201', 'G411'],
      transferStations: ['徐州东换乘'],
      endpoints: null,
    });
  });
});

