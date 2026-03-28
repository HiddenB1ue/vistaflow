import type { SeatClass } from '@/types/route';

const SEAT_LABELS: Record<SeatClass['type'], string> = {
  business: '商务座',
  first: '一等座',
  second: '二等座',
};

export function getSeatLabel(type: SeatClass['type']): string {
  return SEAT_LABELS[type];
}

export function getLowestAvailablePrice(seats: SeatClass[]): number | null {
  const available = seats.filter((s) => s.available);
  if (available.length === 0) return null;
  return Math.min(...available.map((s) => s.price));
}
