
import type { Route, RouteList } from '@/types/route';
import { isTransfer } from '@/types/route';
import type { FilterPrefs } from '@/stores/uiStore';
import { SORT_LABELS } from '@/constants/labels';
import { getLowestAvailablePrice } from '@/utils/seat';

export type SortMode = 'smart' | 'fastest' | 'cheapest';

export const SORT_OPTIONS: Array<{ value: SortMode; label: string }> = [
  { value: 'smart', label: SORT_LABELS.smart },
  { value: 'fastest', label: SORT_LABELS.fastest },
  { value: 'cheapest', label: SORT_LABELS.cheapest },
];

function countTrainSegments(route: Route) {
  return route.segs.filter((segment) => !isTransfer(segment)).length;
}

export function filterAndSortRoutes(routes: RouteList, filterPrefs: FilterPrefs, sortMode: SortMode): RouteList {
  let nextRoutes = [...routes];

  if (filterPrefs.directOnly) {
    nextRoutes = nextRoutes.filter((route) => countTrainSegments(route) === 1);
  }

  if (sortMode === 'fastest') {
    nextRoutes.sort((a, b) => a.durationMinutes - b.durationMinutes);
    return nextRoutes;
  }

  if (sortMode === 'cheapest') {
    nextRoutes.sort((a, b) => {
      const priceA = getLowestAvailablePrice(a.segs.flatMap((segment) => (isTransfer(segment) ? [] : segment.seats))) ?? Number.POSITIVE_INFINITY;
      const priceB = getLowestAvailablePrice(b.segs.flatMap((segment) => (isTransfer(segment) ? [] : segment.seats))) ?? Number.POSITIVE_INFINITY;
      return priceA - priceB;
    });
  }

  return nextRoutes;
}
