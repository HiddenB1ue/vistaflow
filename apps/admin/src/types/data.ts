export type GeoStatusFilter = 'all' | 'missing' | 'complete';
export type GeoSourceFilter = 'all' | 'amap' | 'manual' | 'scraped';
export type SortOrder = 'asc' | 'desc';
export type StationSortBy = 'id' | 'name' | 'geoUpdatedAt' | 'updatedAt';
export type TrainIsActiveFilter = 'all' | 'true' | 'false';
export type TrainSortBy = 'id' | 'trainNo' | 'stationTrainCode' | 'updatedAt';
export type StationGeoSource = 'amap' | 'manual' | 'scraped';

export interface PaginatedResult<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface AdminStationRecord {
  id: string;
  name: string;
  telecode: string;
  pinyin: string | null;
  abbr: string | null;
  areaName: string | null;
  countryName: string | null;
  longitude: number | null;
  latitude: number | null;
  geoSource: StationGeoSource | null;
  geoUpdatedAt: string | null;
  updatedAt: string;
  geoStatus: 'missing' | 'complete';
}

export interface AdminStationListQuery {
  page: number;
  pageSize: number;
  keyword: string;
  geoStatus: GeoStatusFilter;
  geoSource: GeoSourceFilter;
  areaName: string;
  sortBy: StationSortBy;
  sortOrder: SortOrder;
}

export interface AdminStationGeoUpdatePayload {
  longitude: number | null;
  latitude: number | null;
  geoSource: StationGeoSource;
}

export interface AdminTrainRecord {
  id: string;
  trainNo: string;
  stationTrainCode: string | null;
  fromStation: string | null;
  toStation: string | null;
  totalNum: number | null;
  isActive: boolean;
  updatedAt: string;
}

export interface AdminTrainListQuery {
  page: number;
  pageSize: number;
  keyword: string;
  isActive: TrainIsActiveFilter;
  sortBy: TrainSortBy;
  sortOrder: SortOrder;
}

export interface AdminTrainStopRecord {
  stationNo: number;
  stationName: string | null;
  stationTrainCode: string | null;
  arriveTime: string | null;
  startTime: string | null;
  runningTime: string | null;
  arriveDayDiff: number | null;
  arriveDayStr: string | null;
  isStart: string | null;
  startStationName: string | null;
  endStationName: string | null;
  trainClassName: string | null;
  serviceType: string | null;
  wzNum: string | null;
  updatedAt: string;
}
