import type {
  SystemSetting,
  SystemSettingsBatchUpdateRequest,
  SystemSettingsBatchUpdateResponse,
} from '@/types/config';
import { apiClient } from './api';
import { MOCK_SYSTEM_SETTINGS } from './mock/config.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
let mockSettingsState: SystemSetting[] = MOCK_SYSTEM_SETTINGS.map((item) => ({ ...item }));

function cloneSetting(setting: SystemSetting): SystemSetting {
  return {
    ...setting,
    value:
      typeof setting.value === 'object' && setting.value !== null
        ? JSON.parse(JSON.stringify(setting.value))
        : setting.value,
  };
}

export async function fetchSystemSettings(): Promise<SystemSetting[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    return mockSettingsState.map(cloneSetting);
  }
  const { data } = await apiClient.get<{ data: SystemSetting[] }>('/admin/system/settings');
  return data.data;
}

export async function updateSystemSettings(
  payload: SystemSettingsBatchUpdateRequest,
): Promise<SystemSettingsBatchUpdateResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    if (payload.items.length === 0) {
      throw new Error('No system settings to update');
    }
    const updatedAt = new Date().toISOString();
    for (const change of payload.items) {
      const existing = mockSettingsState.find((item) => item.key === change.key);
      if (!existing) {
        throw new Error(`Unknown mock system setting: ${change.key}`);
      }
      const updated = {
        ...existing,
        value: change.value,
        enabled: change.enabled,
        updatedAt,
      };
      mockSettingsState = mockSettingsState.map((item) =>
        item.key === change.key ? updated : item,
      );
    }
    return {
      updatedCount: payload.items.length,
      updatedKeys: payload.items.map((item) => item.key),
      updatedAt,
    };
  }
  const { data } = await apiClient.patch<{ data: SystemSettingsBatchUpdateResponse }>(
    '/admin/system/settings',
    payload,
  );
  return data.data;
}
