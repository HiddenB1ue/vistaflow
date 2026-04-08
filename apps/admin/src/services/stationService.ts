import type { Station } from '@/types/station';
import { apiClient } from './api';
import { MOCK_STATIONS } from './mock/stations.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export async function fetchStations(): Promise<Station[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    return MOCK_STATIONS;
  }
  const { data } = await apiClient.get<{ data: Station[] }>('/stations');
  return data.data;
}
