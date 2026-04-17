import type { JourneyDisplaySortMode } from '@/services/routeService';
import { isTransfer, type Route, type RouteList, type RouteSegment, type TrainSegment } from '@/types/route';
import { getRouteReferencePrice } from '@/utils/seat';

export const SORT_OPTIONS: Array<{ value: JourneyDisplaySortMode; label: string }> = [
  { value: 'duration', label: '总耗时' },
  { value: 'departure', label: '出发时间' },
  { value: 'price', label: '票价' },
];

export interface CollapsedRouteSummary {
  kind: 'direct' | 'transfer';
  trainCodes: string[];
  transferStations: string[];
  endpoints: string | null;
}

function getTrainSegments(route: Route): TrainSegment[] {
  return route.segs.filter((segment): segment is TrainSegment => !isTransfer(segment));
}

function getRouteLowestPrice(route: Route): number | null {
  return getRouteReferencePrice(route);
}

function formatTransferStation(
  segment: RouteSegment,
  previous: TrainSegment | null,
  next: TrainSegment | null,
): string | null {
  if (!isTransfer(segment)) {
    return null;
  }

  const stationName = previous?.destination.name ?? next?.origin.name ?? null;
  if (stationName) {
    return `${stationName}换乘`;
  }

  const rawText = segment.transfer.trim();
  if (!rawText) {
    return null;
  }

  return rawText.split('·')[0]?.trim() || rawText;
}

export function getCollapsedRouteSummary(route: Route): CollapsedRouteSummary {
  const trainSegments = getTrainSegments(route);
  const trainCodes = trainSegments
    .map((segment) => segment.no.trim().toUpperCase())
    .filter(Boolean);

  if (trainCodes.length <= 1) {
    return {
      kind: 'direct',
      trainCodes: trainCodes[0] ? [trainCodes[0]] : [route.trainNo],
      transferStations: [],
      endpoints:
        route.origin.name === route.destination.name
          ? null
          : `${route.origin.name} → ${route.destination.name}`,
    };
  }

  const transferStations = route.segs
    .map((segment, index) => {
      const previous = index > 0 ? route.segs[index - 1] : null;
      const next = index < route.segs.length - 1 ? route.segs[index + 1] : null;
      return formatTransferStation(
        segment,
        previous && !isTransfer(previous) ? previous : null,
        next && !isTransfer(next) ? next : null,
      );
    })
    .filter((value): value is string => Boolean(value));

  return {
    kind: 'transfer',
    trainCodes,
    transferStations,
    endpoints: null,
  };
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
