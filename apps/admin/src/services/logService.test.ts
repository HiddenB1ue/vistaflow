import { describe, it, expect } from 'vitest';
import { fetchLogs } from './logService';

describe('logService', () => {
  it('fetchLogs returns mock data in mock mode', async () => {
    const logs = await fetchLogs();
    expect(Array.isArray(logs)).toBe(true);
    expect(logs.length).toBeGreaterThan(0);
    for (const log of logs) {
      expect(log).toHaveProperty('id');
      expect(log).toHaveProperty('timestamp');
      expect(log).toHaveProperty('severity');
      expect(log).toHaveProperty('message');
    }
  });
});
