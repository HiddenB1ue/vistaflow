import { describe, expect, it } from 'vitest';
import type { SeatClass } from '@/types/route';
import { getLowestAvailablePrice, getSeatLabel } from './seat';

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
