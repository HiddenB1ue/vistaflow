import type { LogRecord } from '@/types/log';
import type { PaginatedResponse, SystemLogsQuery } from '@/types/pagination';
import { apiClient } from './api';
import { MOCK_LOGS } from './mock/logs.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export async function fetchLogs(query: SystemLogsQuery): Promise<PaginatedResponse<LogRecord>> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    // Mock pagination response
    const keyword = query.keyword.trim().toLowerCase();
    const filtered = MOCK_LOGS.filter((log) => {
      const matchesKeyword = keyword.length === 0 || [log.timestamp, log.severity, log.message].some((field) => field.toLowerCase().includes(keyword));
      const matchesSeverity = query.severity === 'all' || log.severity === query.severity;
      return matchesKeyword && matchesSeverity;
    });
    const start = (query.page - 1) * query.pageSize;
    const end = start + query.pageSize;
    const items = filtered.slice(start, end);
    return {
      items,
      page: query.page,
      pageSize: query.pageSize,
      total: filtered.length,
      totalPages: Math.ceil(filtered.length / query.pageSize) || 0,
    };
  }
  const { data } = await apiClient.get<{ data: PaginatedResponse<LogRecord> }>('/admin/system/logs', {
    params: {
      page: query.page,
      pageSize: query.pageSize,
      keyword: query.keyword.trim() || undefined,
      severity: query.severity !== 'all' ? query.severity : undefined,
    },
  });
  return data.data;
}
