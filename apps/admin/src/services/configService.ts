import type {
  SystemSetting,
  SystemSettingsBatchUpdateRequest,
  SystemSettingsBatchUpdateResponse,
} from '@/types/config';
import { apiClient } from './api';

export async function fetchSystemSettings(): Promise<SystemSetting[]> {
  const { data } = await apiClient.get<{ data: SystemSetting[] }>('/admin/system/settings');
  return data.data;
}

export async function updateSystemSettings(
  payload: SystemSettingsBatchUpdateRequest,
): Promise<SystemSettingsBatchUpdateResponse> {
  const { data } = await apiClient.patch<{ data: SystemSettingsBatchUpdateResponse }>(
    '/admin/system/settings',
    payload,
  );
  return data.data;
}
