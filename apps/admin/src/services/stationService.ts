import type { Station } from '@/types/station';
import { apiClient } from './api';
import { MOCK_STATIONS } from './mock/stations.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

interface ApiStation {
  id: number;
  name: string;
  telecode: string;
  pinyin?: string | null;
  abbr?: string | null;
  areaCode?: string | null;
  areaName?: string | null;
  countryCode?: string | null;
  countryName?: string | null;
  longitude?: number | null;
  latitude?: number | null;
  geoSource?: string | null;
  geoUpdatedAt?: string | null;
}

function normalizeDataSource(source?: string | null): Station['dataSource'] {
  if (source === 'manual') return 'manual';
  if (source === 'scraped') return 'scraped';
  return 'amap';
}

function formatUpdatedAt(value?: string | null): string {
  if (!value) {
    return '--';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date).replace(/\//g, '-');
}

function mapApiStation(station: ApiStation): Station {
  const hasCoordinates =
    typeof station.longitude === 'number' && typeof station.latitude === 'number';

  return {
    id: String(station.id),
    name: station.name,
    code: station.telecode,
    city: station.areaName ?? station.countryName ?? '--',
    longitude: hasCoordinates ? station.longitude! : 0,
    latitude: hasCoordinates ? station.latitude! : 0,
    coordinateStatus: hasCoordinates ? 'complete' : 'missing',
    dataSource: normalizeDataSource(station.geoSource),
    lastUpdated: formatUpdatedAt(station.geoUpdatedAt),
  };
}

export async function fetchStations(): Promise<Station[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    return MOCK_STATIONS;
  }
  const { data } = await apiClient.get<{ data: ApiStation[] }>('/stations');
  return data.data.map(mapApiStation);
}
