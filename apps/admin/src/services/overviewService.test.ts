import { beforeEach, describe, expect, it, vi, type Mock } from 'vitest';
import { apiClient } from './api';
import { fetchKpiStats, fetchSparklineData } from './overviewService';

vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('overviewService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchSparklineData requests the sparkline endpoint', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: { data: { values: [1, 2, 3], labels: ['a', 'b', 'c'] } },
    });

    const data = await fetchSparklineData();
    expect(apiClient.get).toHaveBeenCalledWith('/admin/system/overview/sparkline?days=7');
    expect(data.values).toEqual([1, 2, 3]);
  });

  it('fetchKpiStats requests the KPI endpoint', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: {
        data: {
          totalRecords: 1,
          stationsWithCoordinates: 2,
          todayRecordChanges: 3,
          todayTaskRuns: 4,
        },
      },
    });

    const stats = await fetchKpiStats();
    expect(apiClient.get).toHaveBeenCalledWith('/admin/system/overview/kpi');
    expect(stats.totalRecords).toBe(1);
  });
});
