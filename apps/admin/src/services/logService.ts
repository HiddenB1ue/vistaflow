import type { LogRecord } from '@/types/log';
import type { PaginatedResponse, SystemLogsQuery } from '@/types/pagination';
import { apiClient } from './api';

export async function fetchLogs(query: SystemLogsQuery): Promise<PaginatedResponse<LogRecord>> {
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
