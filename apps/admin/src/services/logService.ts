import type { LogRecord } from '@/types/log';
import { apiClient } from './api';
import { MOCK_LOGS } from './mock/logs.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export async function fetchLogs(): Promise<LogRecord[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    return MOCK_LOGS;
  }
  const { data } = await apiClient.get<{ data: LogRecord[] }>('/admin/logs');
  return data.data;
}
