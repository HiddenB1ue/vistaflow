import { describe, expect, it } from 'vitest';
import { routeFixtures } from '@/services/mock/routeFixtures';
import { sortRoutesForDisplay } from './routeList.helpers';

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
