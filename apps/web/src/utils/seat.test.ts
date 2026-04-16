import { describe, expect, it } from 'vitest';
import { routeFixtures } from '@/services/mock/routeFixtures';
import type { SeatClass } from '@/types/route';
import {
  getLowestAvailablePrice,
  getRouteReferencePrice,
  getSeatLabel,
  getSegmentLowestAvailablePrice,
} from './seat';

describe('getSeatLabel', () => {
  it('returns correct label for swz', () => {
    expect(getSeatLabel('swz')).toBe('商务座');
  });

  it('returns correct label for tz', () => {
    expect(getSeatLabel('tz')).toBe('特等座');
  });

  it('returns correct label for wz', () => {
    expect(getSeatLabel('wz')).toBe('无座');
  });

  it('falls back to uppercased raw type', () => {
    expect(getSeatLabel('abc')).toBe('ABC');
  });
});

describe('getLowestAvailablePrice', () => {
  it('returns null for empty array', () => {
    expect(getLowestAvailablePrice([])).toBeNull();
  });

  it('returns null when no seats are available', () => {
    const seats: SeatClass[] = [
      { type: 'swz', label: '商务座', price: 1748, available: false },
      { type: 'zy', label: '一等座', price: 933, available: false },
    ];
    expect(getLowestAvailablePrice(seats)).toBeNull();
  });

  it('ignores null prices', () => {
    const seats: SeatClass[] = [
      { type: 'wz', label: '无座', price: null, available: true },
      { type: 'ze', label: '二等座', price: 553, available: true },
    ];
    expect(getLowestAvailablePrice(seats)).toBe(553);
  });

  it('returns lowest price among available seats', () => {
    const seats: SeatClass[] = [
      { type: 'swz', label: '商务座', price: 1748, available: true },
      { type: 'zy', label: '一等座', price: 933, available: true },
      { type: 'ze', label: '二等座', price: 553, available: false },
    ];
    expect(getLowestAvailablePrice(seats)).toBe(933);
  });
});

describe('getSegmentLowestAvailablePrice', () => {
  it('returns lowest price for a train segment', () => {
    const segment = routeFixtures[0].segs[0];
    if ('transfer' in segment) {
      throw new Error('expected train segment');
    }

    expect(getSegmentLowestAvailablePrice(segment)).toBe(553);
  });
});

describe('getRouteReferencePrice', () => {
  it('returns direct route reference price from its only segment', () => {
    expect(getRouteReferencePrice(routeFixtures[0])).toBe(553);
  });

  it('returns transfer route reference price as per-segment sum', () => {
    expect(getRouteReferencePrice(routeFixtures[3])).toBe(795);
    expect(getRouteReferencePrice(routeFixtures[5])).toBe(680);
  });

  it('returns null when any train segment has no available price', () => {
    const routeWithoutSegmentPrice = {
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

    expect(getRouteReferencePrice(routeWithoutSegmentPrice)).toBeNull();
  });
});
