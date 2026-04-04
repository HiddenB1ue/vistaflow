import { describe, it, expect } from 'vitest';
import { fetchCredentials, fetchToggles } from './configService';

describe('configService', () => {
  it('fetchCredentials returns mock data in mock mode', async () => {
    const creds = await fetchCredentials();
    expect(Array.isArray(creds)).toBe(true);
    expect(creds.length).toBeGreaterThan(0);
    for (const cred of creds) {
      expect(cred).toHaveProperty('id');
      expect(cred).toHaveProperty('name');
      expect(cred).toHaveProperty('health');
    }
  });

  it('fetchToggles returns mock data in mock mode', async () => {
    const toggles = await fetchToggles();
    expect(Array.isArray(toggles)).toBe(true);
    expect(toggles.length).toBeGreaterThan(0);
    for (const toggle of toggles) {
      expect(toggle).toHaveProperty('id');
      expect(toggle).toHaveProperty('label');
      expect(typeof toggle.enabled).toBe('boolean');
    }
  });
});
