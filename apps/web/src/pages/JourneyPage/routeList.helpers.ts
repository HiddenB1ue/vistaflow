import type { JourneyDisplaySortMode } from '@/services/routeService';
import { isTransfer, type Route, type RouteList } from '@/types/route';
import { getRouteReferencePrice } from '@/utils/seat';

export const SORT_OPTIONS: Array<{ value: JourneyDisplaySortMode; label: string }> = [
  { value: 'duration', label: '总耗时' },
  { value: 'departure', label: '出发时间' },
  { value: 'price', label: '票价' },
];

function getRouteLowestPrice(route: Route): number | null {
  return getRouteReferencePrice(route);
}

export function routeHasAvailableTickets(route: Route): boolean {
  let hasTrainSegment = false;

  for (const segment of route.segs) {
    if (isTransfer(segment)) {
      continue;
    }

    hasTrainSegment = true;
    if (!segment.seats.some((seat) => seat.available)) {
      return false;
    }
  }

  return hasTrainSegment;
}

export function sortRoutesForDisplay(routes: RouteList, sortMode: JourneyDisplaySortMode): RouteList {
  const nextRoutes = [...routes];

  if (sortMode === 'price') {
    nextRoutes.sort((left, right) => {
      const leftPrice = getRouteLowestPrice(left);
      const rightPrice = getRouteLowestPrice(right);

      if (leftPrice === null && rightPrice === null) {
        return left.durationMinutes - right.durationMinutes;
      }
      if (leftPrice === null) {
        return 1;
      }
      if (rightPrice === null) {
        return -1;
      }
      if (leftPrice !== rightPrice) {
        return leftPrice - rightPrice;
      }
      if (left.durationMinutes !== right.durationMinutes) {
        return left.durationMinutes - right.durationMinutes;
      }
      return left.departureTime.localeCompare(right.departureTime);
    });
    return nextRoutes;
  }

  if (sortMode === 'departure') {
    nextRoutes.sort((left, right) => left.departureTime.localeCompare(right.departureTime));
    return nextRoutes;
  }

  nextRoutes.sort((left, right) => left.durationMinutes - right.durationMinutes);
  return nextRoutes;
}
