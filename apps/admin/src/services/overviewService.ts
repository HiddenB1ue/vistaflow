import { apiClient } from './api';
import { MOCK_SPARKLINE_DATA, MOCK_API_QUOTA } from './mock/overview.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export type SparklineData = typeof MOCK_SPARKLINE_DATA;
export type ApiQuota = typeof MOCK_API_QUOTA;

export async function fetchSparklineData(): Promise<SparklineData> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    return MOCK_SPARKLINE_DATA;
  }
  const { data } = await apiClient.get<{ data: SparklineData }>('/admin/system/overview/sparkline');
  return data.data;
}

export async function fetchApiQuota(): Promise<ApiQuota> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    return MOCK_API_QUOTA;
  }
  const { data } = await apiClient.get<{ data: ApiQuota }>('/admin/system/overview/quota');
  return data.data;
}
