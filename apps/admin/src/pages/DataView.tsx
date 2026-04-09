import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  AdminStationGeoUpdatePayload,
  AdminStationListQuery,
  AdminStationRecord,
  AdminTrainListQuery,
  AdminTrainRecord,
} from '@/types/data';
import { DATA_LABELS, TOAST_MESSAGES } from '@/constants/labels';
import {
  fetchAdminStations,
  fetchAdminTrains,
  updateAdminStationGeo,
} from '@/services/adminDataService';
import { extractApiErrorMessage } from '@/services/taskService';
import { useToastStore } from '@/stores/toastStore';
import { StationDrawer } from '@/components/overlays/StationDrawer';
import { TrainStopsDrawer } from '@/components/overlays/TrainStopsDrawer';
import {
  Button,
  ContentSection,
  ControlToolbar,
  ControlToolbarActions,
  ControlToolbarMain,
  CustomSelect,
  DataTable,
  DrawerBackdrop,
  InputBox,
  PanelBody,
  PanelCard,
  SegmentedControl,
} from '@vistaflow/ui';
import {
  buildStationColumns,
  buildTrainColumns,
  DATA_TABS,
  SORT_ORDER_OPTIONS,
  STATION_SORT_OPTIONS,
  STATION_SOURCE_OPTIONS,
  STATION_STATUS_OPTIONS,
  stationRowClassName,
  TRAIN_SORT_OPTIONS,
  TRAIN_STATUS_OPTIONS,
  type DataTab,
} from './dataView.config';

const DEFAULT_STATION_QUERY: AdminStationListQuery = {
  page: 1,
  pageSize: 20,
  keyword: '',
  geoStatus: 'all',
  geoSource: 'all',
  areaName: '',
  sortBy: 'updatedAt',
  sortOrder: 'desc',
};

const DEFAULT_TRAIN_QUERY: AdminTrainListQuery = {
  page: 1,
  pageSize: 20,
  keyword: '',
  isActive: 'all',
  sortBy: 'updatedAt',
  sortOrder: 'desc',
};

function parseCoordinateInput(value: string): { value: number | null; valid: boolean } {
  const normalized = value.trim();
  if (normalized.length === 0) {
    return { value: null, valid: true };
  }
  const parsed = Number(normalized);
  if (!Number.isFinite(parsed)) {
    return { value: null, valid: false };
  }
  return { value: parsed, valid: true };
}

function PaginationFooter({
  page,
  totalPages,
  total,
  onPrev,
  onNext,
}: {
  page: number;
  totalPages: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex items-center justify-between border-t border-white/5 px-5 py-4 text-xs text-muted">
      <div className="flex items-center gap-4">
        <span>{DATA_LABELS.recordsCount(total)}</span>
        <span>{DATA_LABELS.pageSummary(page, totalPages)}</span>
      </div>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={onPrev} disabled={page <= 1}>
          {DATA_LABELS.prevPage}
        </Button>
        <Button variant="outline" size="sm" onClick={onNext} disabled={totalPages === 0 || page >= totalPages}>
          {DATA_LABELS.nextPage}
        </Button>
      </div>
    </div>
  );
}

export default function DataView() {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);
  const [activeTab, setActiveTab] = useState<DataTab>('stations');
  const [stationQuery, setStationQuery] = useState<AdminStationListQuery>(DEFAULT_STATION_QUERY);
  const [trainQuery, setTrainQuery] = useState<AdminTrainListQuery>(DEFAULT_TRAIN_QUERY);
  const [selectedStation, setSelectedStation] = useState<AdminStationRecord | null>(null);
  const [selectedTrain, setSelectedTrain] = useState<AdminTrainRecord | null>(null);

  const stationListQuery = useQuery({
    queryKey: ['admin', 'data', 'stations', stationQuery],
    queryFn: () => fetchAdminStations(stationQuery),
  });

  const trainListQuery = useQuery({
    queryKey: ['admin', 'data', 'trains', trainQuery],
    queryFn: () => fetchAdminTrains(trainQuery),
  });

  const stationSaveMutation = useMutation({
    mutationFn: ({
      stationId,
      payload,
    }: {
      stationId: string;
      payload: AdminStationGeoUpdatePayload;
    }) => updateAdminStationGeo(stationId, payload),
    onSuccess: async () => {
      setSelectedStation(null);
      await queryClient.invalidateQueries({ queryKey: ['admin', 'data', 'stations'] });
      addToast(TOAST_MESSAGES.stationSaved, 'success');
    },
    onError: (error) => {
      addToast(extractApiErrorMessage(error), 'error');
    },
  });

  const stationColumns = useMemo(() => buildStationColumns((station) => setSelectedStation(station)), []);
  const trainColumns = useMemo(() => buildTrainColumns((train) => setSelectedTrain(train)), []);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== 'Escape') return;
      setSelectedStation(null);
      setSelectedTrain(null);
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleStationSave = (payload: AdminStationGeoUpdatePayload) => {
    if (!selectedStation) return;
    if (
      (payload.longitude === null && payload.latitude !== null)
      || (payload.longitude !== null && payload.latitude === null)
    ) {
      addToast('经纬度必须同时填写或同时清空', 'error');
      return;
    }
    stationSaveMutation.mutate({
      stationId: selectedStation.id,
      payload,
    });
  };

  const handleStationDrawerSave = (payload: AdminStationGeoUpdatePayload) => {
    const longitudeParsed = parseCoordinateInput(String(payload.longitude ?? ''));
    const latitudeParsed = parseCoordinateInput(String(payload.latitude ?? ''));
    if (!longitudeParsed.valid || !latitudeParsed.valid) {
      addToast('经纬度格式不正确', 'error');
      return;
    }
    handleStationSave({
      longitude: longitudeParsed.value,
      latitude: latitudeParsed.value,
      geoSource: payload.geoSource,
    });
  };

  const activeQuery = activeTab === 'stations' ? stationListQuery : trainListQuery;
  const handleRefresh = async () => {
    await activeQuery.refetch();
    addToast(TOAST_MESSAGES.dataRefreshed, 'info');
  };

  return (
    <div className="vf-page-stack">
      <DrawerBackdrop isActive={selectedStation !== null || selectedTrain !== null} onClick={() => {
        setSelectedStation(null);
        setSelectedTrain(null);
      }} />
      <StationDrawer
        isOpen={selectedStation !== null}
        station={selectedStation}
        saving={stationSaveMutation.isPending}
        onClose={() => setSelectedStation(null)}
        onSave={handleStationDrawerSave}
      />
      <TrainStopsDrawer
        isOpen={selectedTrain !== null}
        train={selectedTrain}
        onClose={() => setSelectedTrain(null)}
      />

      <ContentSection spacing="dense">
        <SegmentedControl
          value={activeTab}
          onChange={(value) => setActiveTab(value as DataTab)}
          options={DATA_TABS.map((tab) => ({ value: tab.id, label: tab.label }))}
        />
      </ContentSection>

      {activeTab === 'stations' ? (
        <ContentSection spacing="dense">
          <ControlToolbar>
            <ControlToolbarMain>
              <InputBox
                placeholder={DATA_LABELS.stationSearchPlaceholder}
                className="min-w-0 w-full"
                value={stationQuery.keyword}
                onChange={(event) => setStationQuery((current) => ({
                  ...current,
                  page: 1,
                  keyword: event.target.value,
                }))}
              />
            </ControlToolbarMain>
            <ControlToolbarActions>
              <Button variant="outline" size="sm" onClick={handleRefresh}>
                {DATA_LABELS.refresh}
              </Button>
            </ControlToolbarActions>
          </ControlToolbar>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <CustomSelect
              options={STATION_STATUS_OPTIONS}
              value={stationQuery.geoStatus}
              onChange={(value) => setStationQuery((current) => ({ ...current, page: 1, geoStatus: value as AdminStationListQuery['geoStatus'] }))}
              className="w-full"
            />
            <CustomSelect
              options={STATION_SOURCE_OPTIONS}
              value={stationQuery.geoSource}
              onChange={(value) => setStationQuery((current) => ({ ...current, page: 1, geoSource: value as AdminStationListQuery['geoSource'] }))}
              className="w-full"
            />
            <InputBox
              placeholder={DATA_LABELS.areaNamePlaceholder}
              className="w-full"
              value={stationQuery.areaName}
              onChange={(event) => setStationQuery((current) => ({ ...current, page: 1, areaName: event.target.value }))}
            />
            <CustomSelect
              options={STATION_SORT_OPTIONS}
              value={stationQuery.sortBy}
              onChange={(value) => setStationQuery((current) => ({ ...current, page: 1, sortBy: value as AdminStationListQuery['sortBy'] }))}
              className="w-full"
            />
            <CustomSelect
              options={SORT_ORDER_OPTIONS}
              value={stationQuery.sortOrder}
              onChange={(value) => setStationQuery((current) => ({ ...current, page: 1, sortOrder: value as AdminStationListQuery['sortOrder'] }))}
              className="w-full"
            />
          </div>

          <PanelCard className="overflow-hidden p-0">
            <PanelBody className="gap-0">
              {stationListQuery.isLoading ? (
                <div className="px-5 py-8 text-sm text-muted">{DATA_LABELS.loading}</div>
              ) : stationListQuery.data && stationListQuery.data.items.length > 0 ? (
                <DataTable
                  columns={stationColumns}
                  data={stationListQuery.data.items}
                  getId={(station) => station.id}
                  rowClassName={stationRowClassName}
                />
              ) : (
                <div className="px-5 py-8 text-sm text-muted">{DATA_LABELS.noStations}</div>
              )}
              <PaginationFooter
                page={stationListQuery.data?.page ?? stationQuery.page}
                totalPages={stationListQuery.data?.totalPages ?? 0}
                total={stationListQuery.data?.total ?? 0}
                onPrev={() => setStationQuery((current) => ({ ...current, page: Math.max(1, current.page - 1) }))}
                onNext={() => setStationQuery((current) => ({ ...current, page: current.page + 1 }))}
              />
            </PanelBody>
          </PanelCard>
        </ContentSection>
      ) : (
        <ContentSection spacing="dense">
          <ControlToolbar>
            <ControlToolbarMain>
              <InputBox
                placeholder={DATA_LABELS.trainSearchPlaceholder}
                className="min-w-0 w-full"
                value={trainQuery.keyword}
                onChange={(event) => setTrainQuery((current) => ({
                  ...current,
                  page: 1,
                  keyword: event.target.value,
                }))}
              />
            </ControlToolbarMain>
            <ControlToolbarActions>
              <Button variant="outline" size="sm" onClick={handleRefresh}>
                {DATA_LABELS.refresh}
              </Button>
            </ControlToolbarActions>
          </ControlToolbar>

          <div className="grid gap-3 md:grid-cols-3">
            <CustomSelect
              options={TRAIN_STATUS_OPTIONS}
              value={trainQuery.isActive}
              onChange={(value) => setTrainQuery((current) => ({ ...current, page: 1, isActive: value as AdminTrainListQuery['isActive'] }))}
              className="w-full"
            />
            <CustomSelect
              options={TRAIN_SORT_OPTIONS}
              value={trainQuery.sortBy}
              onChange={(value) => setTrainQuery((current) => ({ ...current, page: 1, sortBy: value as AdminTrainListQuery['sortBy'] }))}
              className="w-full"
            />
            <CustomSelect
              options={SORT_ORDER_OPTIONS}
              value={trainQuery.sortOrder}
              onChange={(value) => setTrainQuery((current) => ({ ...current, page: 1, sortOrder: value as AdminTrainListQuery['sortOrder'] }))}
              className="w-full"
            />
          </div>

          <PanelCard className="overflow-hidden p-0">
            <PanelBody className="gap-0">
              {trainListQuery.isLoading ? (
                <div className="px-5 py-8 text-sm text-muted">{DATA_LABELS.loading}</div>
              ) : trainListQuery.data && trainListQuery.data.items.length > 0 ? (
                <DataTable
                  columns={trainColumns}
                  data={trainListQuery.data.items}
                  getId={(train) => train.id}
                />
              ) : (
                <div className="px-5 py-8 text-sm text-muted">{DATA_LABELS.noTrains}</div>
              )}
              <PaginationFooter
                page={trainListQuery.data?.page ?? trainQuery.page}
                totalPages={trainListQuery.data?.totalPages ?? 0}
                total={trainListQuery.data?.total ?? 0}
                onPrev={() => setTrainQuery((current) => ({ ...current, page: Math.max(1, current.page - 1) }))}
                onNext={() => setTrainQuery((current) => ({ ...current, page: current.page + 1 }))}
              />
            </PanelBody>
          </PanelCard>
        </ContentSection>
      )}
    </div>
  );
}
