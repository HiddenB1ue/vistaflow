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
  type: 'business' | 'first' | 'second';
  label: string;
  price: number;
  available: boolean;
  /** 可选余票文本，如「仅剩 1 席」「余 2 席」，未提供时用默认值 */
  availabilityText?: string;
}

export interface TrainSegment {
  no: string;
  origin: Station;
  destination: Station;
  departureTime: string;
  arrivalTime: string;
  stops: TrainStop[];
  seats: SeatClass[];
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
  /** 方案类型标签，如「最优直达」「省时中转 (1次)」 */
  type: string;
  origin: Station;
  destination: Station;
  departureTime: string;
  arrivalTime: string;
  durationMinutes: number;
  /** 行程段列表：TrainSegment | TransferSegment 交替出现 */
  segs: RouteSegment[];
  /** GCJ-02 坐标路径点，用于地图绘制 */
  pathPoints: Array<{ lng: number; lat: number }>;
}

export type RouteList = Route[];
