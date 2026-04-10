import { apiClient } from './api';
import type { ActiveTask, ApiQuota, KpiStats, SparklineData, SystemAlert } from '@/types/overview';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export async function fetchSparklineData(days: number = 7): Promise<SparklineData> {
  const { data } = await apiClient.get<{ data: SparklineData }>(`/admin/system/overview/sparkline?days=${days}`);
  return data.data;
}

export async function fetchApiQuota(): Promise<ApiQuota> {
  const { data } = await apiClient.get<{ data: ApiQuota }>('/admin/system/overview/quota');
  return data.data;
}

export async function fetchKpiStats(): Promise<KpiStats> {
  const { data } = await apiClient.get<{ data: KpiStats }>('/admin/system/overview/kpi');
  return data.data;
}

export async function fetchActiveTasks(): Promise<ActiveTask[]> {
  const { data } = await apiClient.get<{ data: ActiveTask[] }>('/admin/system/overview/tasks');
  return data.data;
}

export async function fetchSystemAlerts(): Promise<SystemAlert[]> {
  const { data } = await apiClient.get<{ data: SystemAlert[] }>('/admin/system/overview/alerts');
  return data.data;
}
