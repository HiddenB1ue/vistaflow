import type { AdminStationRecord, AdminTrainRecord, AdminTrainStopRecord } from '@/types/data';
import { DATA_LABELS } from '@/constants/labels';
import { Badge, Button } from '@vistaflow/ui';

export type DataTab = 'stations' | 'trains';

export const DATA_TABS: Array<{ id: DataTab; label: string }> = [
  { id: 'stations', label: DATA_LABELS.stationData },
  { id: 'trains', label: DATA_LABELS.trainData },
];

export const STATION_STATUS_OPTIONS = [
  { value: 'all', label: DATA_LABELS.allStatus },
  { value: 'complete', label: DATA_LABELS.coordComplete },
  { value: 'missing', label: DATA_LABELS.coordMissing },
];

export const STATION_SOURCE_OPTIONS = [
  { value: 'all', label: DATA_LABELS.allSources },
  { value: 'amap', label: DATA_LABELS.sourceAmap },
  { value: 'manual', label: DATA_LABELS.sourceManual },
  { value: 'scraped', label: DATA_LABELS.sourceScraped },
];

export const STATION_SORT_OPTIONS = [
  { value: 'updatedAt', label: DATA_LABELS.sortUpdatedAt },
  { value: 'geoUpdatedAt', label: DATA_LABELS.sortGeoUpdatedAt },
  { value: 'name', label: DATA_LABELS.sortName },
  { value: 'id', label: DATA_LABELS.sortId },
];

export const TRAIN_STATUS_OPTIONS = [
  { value: 'all', label: DATA_LABELS.allTrains },
  { value: 'true', label: DATA_LABELS.activeTrains },
  { value: 'false', label: DATA_LABELS.inactiveTrains },
];

export const TRAIN_SORT_OPTIONS = [
  { value: 'updatedAt', label: DATA_LABELS.sortUpdatedAt },
  { value: 'trainNo', label: DATA_LABELS.sortTrainNo },
  { value: 'stationTrainCode', label: DATA_LABELS.sortStationTrainCode },
  { value: 'id', label: DATA_LABELS.sortId },
];

export const SORT_ORDER_OPTIONS = [
  { value: 'desc', label: DATA_LABELS.descOrder },
  { value: 'asc', label: DATA_LABELS.ascOrder },
];

const coordColorMap: Record<string, string> = {
  complete: 'text-[#4ADE80]',
  missing: 'text-red-400',
};

const statusBadgeMap: Record<string, { variant: 'green' | 'yellow' | 'red'; label: string }> = {
  complete: { variant: 'green', label: DATA_LABELS.statusComplete },
  missing: { variant: 'red', label: DATA_LABELS.statusMissing },
};

export function formatCoordinate(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(6) : '--';
}

export function buildStationColumns(onEdit: (station: AdminStationRecord) => void) {
  return [
    {
      key: 'name',
      header: '站点名称',
      render: (station: AdminStationRecord) => (
        <span className={`font-medium ${station.geoStatus === 'missing' ? 'text-red-300' : 'text-white'}`}>
          {station.name}
        </span>
      ),
    },
    {
      key: 'telecode',
      header: '电报码',
      render: (station: AdminStationRecord) => <span className="font-mono text-xs text-muted">{station.telecode}</span>,
    },
    {
      key: 'areaName',
      header: '所属区域',
      render: (station: AdminStationRecord) => station.areaName ?? DATA_LABELS.unknown,
    },
    {
      key: 'lng',
      header: '经度',
      render: (station: AdminStationRecord) => <span className={`font-mono text-xs ${coordColorMap[station.geoStatus] ?? ''}`}>{formatCoordinate(station.longitude)}</span>,
    },
    {
      key: 'lat',
      header: '纬度',
      render: (station: AdminStationRecord) => <span className={`font-mono text-xs ${coordColorMap[station.geoStatus] ?? ''}`}>{formatCoordinate(station.latitude)}</span>,
    },
    {
      key: 'status',
      header: '坐标状态',
      render: (station: AdminStationRecord) => {
        const badge = statusBadgeMap[station.geoStatus];
        return badge ? <Badge variant={badge.variant}>{badge.label}</Badge> : null;
      },
    },
    {
      key: 'source',
      header: '来源',
      render: (station: AdminStationRecord) => (
        <span className="text-xs text-muted">{station.geoSource ?? DATA_LABELS.unknown}</span>
      ),
    },
    {
      key: 'updated',
      header: '最近更新',
      render: (station: AdminStationRecord) => <span className="text-xs text-muted">{station.updatedAt}</span>,
    },
    {
      key: 'action',
      header: '操作',
      className: 'text-center',
      render: (station: AdminStationRecord) => (
        <Button variant={station.geoStatus === 'missing' ? 'warning' : 'outline'} size="sm" onClick={() => onEdit(station)}>
          {station.geoStatus === 'missing' ? DATA_LABELS.editGeo : DATA_LABELS.view}
        </Button>
      ),
    },
  ];
}

export function buildTrainColumns(onViewStops: (train: AdminTrainRecord) => void) {
  return [
    {
      key: 'trainNo',
      header: 'train_no',
      render: (train: AdminTrainRecord) => (
        <span className="font-mono text-xs text-white">{train.trainNo}</span>
      ),
    },
    {
      key: 'stationTrainCode',
      header: '车次号',
      render: (train: AdminTrainRecord) => train.stationTrainCode ?? DATA_LABELS.unknown,
    },
    {
      key: 'fromStation',
      header: '始发站',
      render: (train: AdminTrainRecord) => train.fromStation ?? DATA_LABELS.unknown,
    },
    {
      key: 'toStation',
      header: '终到站',
      render: (train: AdminTrainRecord) => train.toStation ?? DATA_LABELS.unknown,
    },
    {
      key: 'totalNum',
      header: '经停总数',
      render: (train: AdminTrainRecord) => (
        <span className="font-mono text-xs text-muted">
          {typeof train.totalNum === 'number' ? train.totalNum : DATA_LABELS.unknown}
        </span>
      ),
    },
    {
      key: 'status',
      header: '状态',
      render: (train: AdminTrainRecord) => (
        <Badge variant={train.isActive ? 'green' : 'red'}>
          {train.isActive ? DATA_LABELS.activeTrains : DATA_LABELS.inactiveTrains}
        </Badge>
      ),
    },
    {
      key: 'updatedAt',
      header: '最近更新',
      render: (train: AdminTrainRecord) => (
        <span className="text-xs text-muted">{train.updatedAt}</span>
      ),
    },
    {
      key: 'action',
      header: '操作',
      className: 'text-center',
      render: (train: AdminTrainRecord) => (
        <Button variant="outline" size="sm" onClick={() => onViewStops(train)}>
          {DATA_LABELS.viewStops}
        </Button>
      ),
    },
  ];
}

export function buildTrainStopColumns() {
  return [
    {
      key: 'stationNo',
      header: '站序',
      render: (stop: AdminTrainStopRecord) => (
        <span className="font-mono text-xs text-muted">{stop.stationNo}</span>
      ),
    },
    {
      key: 'stationName',
      header: '站点名称',
      render: (stop: AdminTrainStopRecord) => stop.stationName ?? DATA_LABELS.unknown,
    },
    {
      key: 'arriveTime',
      header: '到达',
      render: (stop: AdminTrainStopRecord) => stop.arriveTime ?? DATA_LABELS.unknown,
    },
    {
      key: 'startTime',
      header: '发车',
      render: (stop: AdminTrainStopRecord) => stop.startTime ?? DATA_LABELS.unknown,
    },
    {
      key: 'runningTime',
      header: '运行时长',
      render: (stop: AdminTrainStopRecord) => stop.runningTime ?? DATA_LABELS.unknown,
    },
    {
      key: 'arriveDayStr',
      header: '到达描述',
      render: (stop: AdminTrainStopRecord) => stop.arriveDayStr ?? DATA_LABELS.unknown,
    },
  ];
}

export function stationRowClassName(station: AdminStationRecord) {
  if (station.geoStatus === 'missing') return 'bg-[#F87171]/[0.03]';
  return '';
}
