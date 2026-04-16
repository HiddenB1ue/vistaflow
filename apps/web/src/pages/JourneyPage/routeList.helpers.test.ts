import { describe, expect, it } from 'vitest';
import { routeFixtures } from '@/services/mock/routeFixtures';
import { sortRoutesForDisplay } from './routeList.helpers';

describe('sortRoutesForDisplay', () => {
  it('sorts routes by lowest available price on the current result set', () => {
    const sorted = sortRoutesForDisplay(routeFixtures, 'price');

    expect(sorted.map((route) => route.id)).toEqual([
      'G105-R',
      'G107',
      'G101',
      'G1',
      'G21',
      'G103',
    ]);
  });

  it('pushes routes without available prices to the end', () => {
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

    expect(sorted.map((route) => route.id)).toEqual(['G105-R', 'G1', 'no-price']);
  });
});
