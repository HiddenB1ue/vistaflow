import { describe, it, expect } from 'vitest';
import { fetchSystemSettings, updateSystemSettings } from './configService';

describe('configService', () => {
  it('fetchSystemSettings returns mock data in mock mode', async () => {
    const settings = await fetchSystemSettings();
    expect(Array.isArray(settings)).toBe(true);
    expect(settings.length).toBeGreaterThan(0);
    for (const item of settings) {
      expect(item).toHaveProperty('key');
      expect(item).toHaveProperty('valueType');
      expect(item).toHaveProperty('enabled');
    }
  });

  it('updateSystemSettings returns updated mock result in mock mode', async () => {
    const updated = await updateSystemSettings({
      items: [{ key: 'maintenance_mode', value: true, enabled: true }],
    });
    expect(updated.updatedCount).toBe(1);
    expect(updated.updatedKeys).toEqual(['maintenance_mode']);
  });
});
