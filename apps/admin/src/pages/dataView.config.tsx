import type { Station } from '@/types/station';
import { DATA_LABELS } from '@/constants/labels';
import { Badge, Button } from '@vistaflow/ui';

export type DataTab = 'stations' | 'routes' | 'price';

export const DATA_TABS: Array<{ id: DataTab; label: string }> = [
  { id: 'stations', label: DATA_LABELS.stationData },
  { id: 'routes', label: DATA_LABELS.routeData },
  { id: 'price', label: DATA_LABELS.priceMatrix },
];

export const STATUS_OPTIONS = [
  { value: 'all', label: DATA_LABELS.allStatus },
  { value: 'complete', label: DATA_LABELS.coordComplete },
  { value: 'low-confidence', label: DATA_LABELS.lowConfidence },
  { value: 'missing', label: DATA_LABELS.coordMissing },
];

const coordColorMap: Record<string, string> = {
  complete: 'text-[#4ADE80]',
  'low-confidence': 'text-[#FACC15]',
  missing: 'text-red-400',
};

const statusBadgeMap: Record<string, { variant: 'green' | 'yellow' | 'red'; label: string }> = {
  complete: { variant: 'green', label: DATA_LABELS.statusComplete },
  'low-confidence': { variant: 'yellow', label: DATA_LABELS.lowConfidence },
  missing: { variant: 'red', label: DATA_LABELS.statusMissing },
};

export function buildStationColumns(onEdit: (station: Station) => void) {
  return [
    {
      key: 'name',
      header: '站点名称',
      render: (station: Station) => (
        <span className={`font-medium ${station.coordinateStatus === 'missing' ? 'text-red-300' : 'text-white'}`}>
          {station.name}
        </span>
      ),
    },
    {
      key: 'code',
      header: '编码',
      render: (station: Station) => <span className="font-mono text-xs text-muted">{station.code}</span>,
    },
    {
      key: 'city',
      header: '所属城市',
      render: (station: Station) => station.city,
    },
    {
      key: 'lng',
      header: '经度',
      render: (station: Station) => <span className={`font-mono text-xs ${coordColorMap[station.coordinateStatus] ?? ''}`}>{station.longitude.toFixed(6)}</span>,
    },
    {
      key: 'lat',
      header: '纬度',
      render: (station: Station) => <span className={`font-mono text-xs ${coordColorMap[station.coordinateStatus] ?? ''}`}>{station.latitude.toFixed(6)}</span>,
    },
    {
      key: 'status',
      header: '坐标状态',
      render: (station: Station) => {
        const badge = statusBadgeMap[station.coordinateStatus];
        return badge ? <Badge variant={badge.variant}>{badge.label}</Badge> : null;
      },
    },
    {
      key: 'updated',
      header: '最近更新',
      render: (station: Station) => <span className="text-xs text-muted">{station.lastUpdated}</span>,
    },
    {
      key: 'action',
      header: '操作',
      className: 'text-center',
      render: (station: Station) => (
        station.coordinateStatus === 'low-confidence'
          ? <Button variant="warning" size="sm" onClick={() => onEdit(station)}>{DATA_LABELS.verify}</Button>
          : <Button variant="outline" size="sm" onClick={() => onEdit(station)}>{DATA_LABELS.edit}</Button>
      ),
    },
  ];
}

export function stationRowClassName(station: Station) {
  if (station.coordinateStatus === 'low-confidence') return 'bg-[#FACC15]/[0.03]';
  if (station.coordinateStatus === 'missing') return 'bg-[#F87171]/[0.03]';
  return '';
}
