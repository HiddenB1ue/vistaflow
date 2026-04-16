import type { BaseStation } from '@vistaflow/types';

export interface Station extends BaseStation {
  /** GCJ-02 坐标（已在 services 层转换） */
  lng: number;
  lat: number;
}

export interface TrainStop {
  station: Station;
  arrivalTime: string | null;
  departureTime: string | null;
  stopDuration: number | null;
}

export interface SeatClass {
  type: string;
  label: string;
  price: number | null;
  available: boolean;
  /** 可选余票文本，如「仅剩 1 席」「余 2 席」，未提供时用默认值 */
  availabilityText?: string;
}

export interface TrainSegment {
  trainNo: string;
  no: string;
  origin: Station;
  destination: Station;
  departureTime: string;
  arrivalTime: string;
  stops: TrainStop[];
  stopsCount?: number;
  seats: SeatClass[];
  ticketStatus?: 'ready' | 'unavailable' | 'disabled';
}

interface TransferSegment {
  transfer: string;
}

export type RouteSegment = TrainSegment | TransferSegment;

export function isTransfer(seg: RouteSegment): seg is TransferSegment {
  return 'transfer' in seg;
}

export interface Route {
  id: string;
  trainNo: string;
  type: string;
  origin: Station;
  destination: Station;
  departureTime: string;
  arrivalTime: string;
  durationMinutes: number;
  segs: RouteSegment[];
  pathPoints: Array<{ lng: number; lat: number }>;
  ticketStatus?: 'ready' | 'partial' | 'unavailable' | 'disabled';
}

export type RouteList = Route[];
