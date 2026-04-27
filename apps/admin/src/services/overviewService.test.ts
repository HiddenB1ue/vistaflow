import { describe, it, expect } from 'vitest';
import { fetchKpiStats, fetchSparklineData } from './overviewService';

describe('overviewService', () => {
  it('fetchSparklineData returns mock data in mock mode', async () => {
    const data = await fetchSparklineData();
    expect(data).toHaveProperty('values');
    expect(data).toHaveProperty('labels');
    expect(Array.isArray(data.values)).toBe(true);
  });

  it('fetchKpiStats returns real KPI fields', async () => {
    const stats = await fetchKpiStats();
    expect(stats).toHaveProperty('totalRecords');
    expect(stats).toHaveProperty('stationsWithCoordinates');
    expect(stats).toHaveProperty('todayRecordChanges');
    expect(stats).toHaveProperty('todayTaskRuns');
    expect(stats).not.toHaveProperty('remainingQuota');
  });
});
