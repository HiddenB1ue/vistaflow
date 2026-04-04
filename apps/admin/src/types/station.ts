import type { BaseStation } from '@vistaflow/types';

type CoordinateStatus = 'complete' | 'low-confidence' | 'missing';

export interface Station extends BaseStation {
  id: string;
  longitude: number;
  latitude: number;
  coordinateStatus: CoordinateStatus;
  confidence?: number;
  dataSource: 'amap' | 'manual' | 'scraped';
  lastUpdated: string;
  notes?: string;
}

export interface StationPreview {
  id: string;
  name: string;
  code: string;
  longitude: number;
  latitude: number;
  confidence: number | null;
  failed: boolean;
}
