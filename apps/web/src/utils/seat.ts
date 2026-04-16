import type { Route, SeatClass, TrainSegment } from '@/types/route';

const SEAT_LABELS: Record<string, string> = {
  swz: '商务座',
  tz: '特等座',
  zy: '一等座',
  ze: '二等座',
  gr: '高级软卧',
  rw: '软卧',
  yw: '硬卧',
  yz: '硬座',
  wz: '无座',
  gg: '其他',
};

export function getSeatLabel(type: SeatClass['type']): string {
  return SEAT_LABELS[type.trim().toLowerCase()] ?? type.toUpperCase();
}

export function getLowestAvailablePrice(seats: SeatClass[]): number | null {
  let lowestPrice: number | null = null;

  for (const seat of seats) {
    if (!seat.available || seat.price === null) {
      continue;
    }
    if (lowestPrice === null || seat.price < lowestPrice) {
      lowestPrice = seat.price;
    }
  }

  return lowestPrice;
}

export function getSegmentLowestAvailablePrice(segment: TrainSegment): number | null {
  return getLowestAvailablePrice(segment.seats);
}

export function getRouteReferencePrice(route: Route): number | null {
  let totalPrice = 0;
  let hasTrainSegment = false;

  for (const segment of route.segs) {
    if ('transfer' in segment) {
      continue;
    }
    hasTrainSegment = true;
    const segmentPrice = getSegmentLowestAvailablePrice(segment);
    if (segmentPrice === null) {
      return null;
    }
    totalPrice += segmentPrice;
  }

  return hasTrainSegment ? totalPrice : null;
}
