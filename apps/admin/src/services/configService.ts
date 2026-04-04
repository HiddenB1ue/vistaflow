import type { ApiCredential, GlobalToggle } from '@/types/config';
import { apiClient } from './api';
import { MOCK_CREDENTIALS, MOCK_TOGGLES } from './mock/config.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export async function fetchCredentials(): Promise<ApiCredential[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    return MOCK_CREDENTIALS;
  }
  const { data } = await apiClient.get<{ data: ApiCredential[] }>('/admin/credentials');
  return data.data;
}

export async function fetchToggles(): Promise<GlobalToggle[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    return MOCK_TOGGLES;
  }
  const { data } = await apiClient.get<{ data: GlobalToggle[] }>('/admin/toggles');
  return data.data;
}
