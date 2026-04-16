import type { SeatClass } from '@/types/route';

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
