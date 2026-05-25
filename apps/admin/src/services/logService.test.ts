import { beforeEach, describe, expect, it, vi, type Mock } from 'vitest';
import { apiClient } from './api';
import { fetchLogs } from './logService';
import type { LogRecord } from '@/types/log';

vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const sampleLog: LogRecord = {
  id: '1',
  timestamp: '2026-01-01T00:00:00Z',
  severity: 'INFO',
  message: 'System started',
  highlightedTerms: [],
};

describe('logService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchLogs forwards filters to the API', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: {
        data: {
          items: [sampleLog],
          page: 1,
          pageSize: 20,
          total: 1,
          totalPages: 1,
        },
      },
    });

    const logs = await fetchLogs({
      page: 1,
      pageSize: 20,
      keyword: ' system ',
      severity: 'INFO',
    });

    expect(apiClient.get).toHaveBeenCalledWith('/admin/system/logs', {
      params: {
        page: 1,
        pageSize: 20,
        keyword: 'system',
        severity: 'INFO',
      },
    });
    expect(logs.items).toEqual([sampleLog]);
  });
});
