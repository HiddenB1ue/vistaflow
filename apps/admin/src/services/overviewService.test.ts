import { describe, it, expect } from 'vitest';
import { fetchSparklineData, fetchApiQuota } from './overviewService';

describe('overviewService', () => {
  it('fetchSparklineData returns mock data in mock mode', async () => {
    const data = await fetchSparklineData();
    expect(data).toHaveProperty('values');
    expect(data).toHaveProperty('labels');
    expect(Array.isArray(data.values)).toBe(true);
  });

  it('fetchApiQuota returns mock data in mock mode', async () => {
    const quota = await fetchApiQuota();
    expect(quota).toHaveProperty('percentage');
    expect(quota).toHaveProperty('used');
    expect(quota).toHaveProperty('total');
  });
});
