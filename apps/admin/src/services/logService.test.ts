import { describe, it, expect } from 'vitest';
import { fetchLogs } from './logService';

describe('logService', () => {
  it('fetchLogs returns mock data in mock mode', async () => {
    const logs = await fetchLogs({
      page: 1,
      pageSize: 20,
      keyword: '',
      severity: 'all',
    });
    expect(Array.isArray(logs.items)).toBe(true);
    expect(logs.items.length).toBeGreaterThan(0);
    for (const log of logs.items) {
      expect(log).toHaveProperty('id');
      expect(log).toHaveProperty('timestamp');
      expect(log).toHaveProperty('severity');
      expect(log).toHaveProperty('message');
    }
  });
});
