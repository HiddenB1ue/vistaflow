import { describe, expect, it } from 'vitest';
import type { SeatClass } from '@/types/route';
import { getLowestAvailablePrice, getSeatLabel } from './seat';

describe('getSeatLabel', () => {
  it('returns correct label for business', () => {
    expect(getSeatLabel('business')).toBe('商务座');
  });

  it('returns correct label for first', () => {
    expect(getSeatLabel('first')).toBe('一等座');
  });

  it('returns correct label for second', () => {
    expect(getSeatLabel('second')).toBe('二等座');
  });
});

describe('getLowestAvailablePrice', () => {
  it('returns null for empty array', () => {
    expect(getLowestAvailablePrice([])).toBeNull();
  });

  it('returns null when no seats are available', () => {
    const seats: SeatClass[] = [
      { type: 'business', label: '商务座', price: 1748, available: false },
      { type: 'first', label: '一等座', price: 933, available: false },
    ];
    expect(getLowestAvailablePrice(seats)).toBeNull();
  });

  it('returns lowest price among available seats', () => {
    const seats: SeatClass[] = [
      { type: 'business', label: '商务座', price: 1748, available: true },
      { type: 'first', label: '一等座', price: 933, available: true },
      { type: 'second', label: '二等座', price: 553, available: false },
    ];
    expect(getLowestAvailablePrice(seats)).toBe(933);
  });

  it('returns the only available price', () => {
    const seats: SeatClass[] = [
      { type: 'second', label: '二等座', price: 553, available: true },
    ];
    expect(getLowestAvailablePrice(seats)).toBe(553);
  });
});
