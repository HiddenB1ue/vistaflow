import { beforeEach, describe, expect, it, vi, type Mock } from 'vitest';
import { apiClient } from './api';
import { fetchSystemSettings, updateSystemSettings } from './configService';
import type { SystemSetting } from '@/types/config';

vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

const sampleSetting: SystemSetting = {
  key: 'maintenance_mode',
  label: 'Maintenance mode',
  description: 'Disable public search',
  value: false,
  valueType: 'bool',
  category: 'system',
  enabled: true,
  updatedAt: '2026-01-01T00:00:00Z',
};

describe('configService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchSystemSettings unwraps the API response', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: { data: [sampleSetting] } });

    const settings = await fetchSystemSettings();
    expect(apiClient.get).toHaveBeenCalledWith('/admin/system/settings');
    expect(settings).toEqual([sampleSetting]);
  });

  it('updateSystemSettings patches settings and unwraps the API response', async () => {
    (apiClient.patch as Mock).mockResolvedValueOnce({
      data: {
        data: {
          updatedCount: 1,
          updatedKeys: ['maintenance_mode'],
          updatedAt: '2026-01-01T00:00:00Z',
        },
      },
    });
    const payload = {
      items: [{ key: 'maintenance_mode', value: true, enabled: true }],
    };

    const updated = await updateSystemSettings({
      items: [{ key: 'maintenance_mode', value: true, enabled: true }],
    });
    expect(apiClient.patch).toHaveBeenCalledWith('/admin/system/settings', payload);
    expect(updated.updatedCount).toBe(1);
    expect(updated.updatedKeys).toEqual(['maintenance_mode']);
  });
});
